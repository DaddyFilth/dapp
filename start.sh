#!/bin/bash
# Production startup script for LeadService

set -e

cd ~/dapp/leadservice

echo "🚀 LeadService Production Startup"
echo "=================================="

# 1. Initialize database
echo "[1/4] Initializing database..."
python3 -c "
import sqlite3
import os

os.makedirs('data', exist_ok=True)
conn = sqlite3.connect('data/leadservice.db')

# Create all tables
conn.executescript('''
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT,
        tvl REAL DEFAULT 0,
        volume_24h REAL DEFAULT 0,
        chain TEXT,
        website TEXT,
        twitter TEXT,
        email TEXT,
        rank INTEGER,
        priority TEXT,
        score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        lead_name TEXT NOT NULL,
        subject TEXT,
        body TEXT,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        lead_name TEXT NOT NULL,
        meeting_date TEXT,
        meeting_time TEXT,
        notes TEXT,
        status TEXT DEFAULT 'scheduled',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        draft_id INTEGER,
        lead_name TEXT NOT NULL,
        reply_text TEXT,
        sentiment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')

conn.commit()
conn.close()
print('✅ Database initialized')
"

# 2. Scrape leads if none exist
echo "[2/4] Checking leads..."
LEAD_COUNT=$(python3 -c "import sqlite3; c=sqlite3.connect('data/leadservice.db'); print(c.execute('SELECT COUNT(*) FROM leads').fetchone()[0]); c.close()")

if [ "$LEAD_COUNT" -eq 0 ]; then
    echo "📊 No leads found. Scraping DefiLlama..."
    python3 scripts/scrape_defillama.py
    
    if [ -f "data/defi_leads.csv" ]; then
        echo "📝 Importing scraped leads..."
        python3 -c "
import sqlite3
import csv

conn = sqlite3.connect('data/leadservice.db')
count = 0

with open('data/defi_leads.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            tvl = float(row.get('tvl', 0) or 0)
            volume = float(row.get('volume_24h', 0) or 0)
            priority = 'high' if tvl > 100 else 'medium' if tvl > 10 else 'low'
            score = min(100, tvl * 0.5 + volume * 0.3)
            
            conn.execute('''
                INSERT OR IGNORE INTO leads (name, category, tvl, volume_24h, chain, website, twitter, priority, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('name', ''),
                row.get('category', 'dex'),
                tvl,
                volume,
                row.get('chain', 'multi'),
                row.get('website', ''),
                row.get('twitter', ''),
                priority,
                score
            ))
            count += 1
        except Exception as e:
            print(f'Skip: {e}')

conn.commit()
conn.close()
print(f'✅ Imported {count} leads')
"
    else
        echo "⚠️  No CSV found. Creating sample data..."
        python3 -c "
import sqlite3
conn = sqlite3.connect('data/leadservice.db')
samples = [
    ('Uniswap', 'dex', 4500, 1200, 'Ethereum', 'https://uniswap.org', '@Uniswap', 'high', 95),
    ('Aave', 'lending', 3200, 800, 'Ethereum', 'https://aave.com', '@AaveAave', 'high', 92),
    ('Curve', 'dex', 2800, 600, 'Ethereum', 'https://curve.fi', '@CurveFinance', 'high', 88),
    ('Lido', 'yield', 2500, 400, 'Ethereum', 'https://lido.fi', '@LidoFinance', 'high', 85),
    ('MakerDAO', 'lending', 1800, 300, 'Ethereum', 'https://makerdao.com', '@MakerDAO', 'high', 82),
]
for s in samples:
    conn.execute('INSERT OR IGNORE INTO leads (name, category, tvl, volume_24h, chain, website, twitter, priority, score) VALUES (?,?,?,?,?,?,?,?,?)', s)
conn.commit()
conn.close()
print('✅ Sample data created')
"
    fi
else
    echo "✓ Found $LEAD_COUNT leads"
fi

# 3. Generate drafts if none exist
echo "[3/4] Checking drafts..."
DRAFT_COUNT=$(python3 -c "import sqlite3; c=sqlite3.connect('data/leadservice.db'); print(c.execute('SELECT COUNT(*) FROM drafts').fetchone()[0]); c.close()")

if [ "$DRAFT_COUNT" -eq 0 ]; then
    echo "📧 Generating drafts..."
    python3 -c "
import sqlite3
conn = sqlite3.connect('data/leadservice.db')
leads = conn.execute('SELECT * FROM leads').fetchall()
count = 0
for lead in leads:
    conn.execute('''
        INSERT INTO drafts (lead_id, lead_name, subject, body)
        VALUES (?, ?, ?, ?)
    ''', (
        lead[0],
        lead[1],
        f'Partnership Opportunity with {lead[1]}',
        f'Hi {lead[1]} team,\
\
Impressed by your ${lead[3]}M TVL.\
\
Best regards,\
Partnership Team'
    ))
    count += 1
conn.commit()
conn.close()
print(f'✅ Generated {count} drafts')
"
else
    echo "✓ Found $DRAFT_COUNT drafts"
fi

# 4. Start backend
echo "[4/4] Starting backend server..."
cd backend
exec python main.py
