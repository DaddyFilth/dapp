#!/bin/bash
# Auto-start LeadService - Pull leads and generate drafts

cd ~/dapp/leadservice

echo "=== Starting LeadService ==="

# 1. Start backend
echo "Starting backend..."
cd backend
pkill -f "python.*main.py" 2>/dev/null
sleep 1
python main.py &
sleep 3

# 2. Check if we have leads
cd ~/dapp/leadservice
LEAD_COUNT=$(sqlite3 data/leadservice.db "SELECT COUNT(*) FROM leads;" 2>/dev/null || echo "0")
echo "Current leads: $LEAD_COUNT"

# 3. If no leads, scrape from DefiLlama
if [ "$LEAD_COUNT" -eq 0 ]; then
    echo "No leads found. Scraping DefiLlama..."
    python scripts/scrape_defillama.py
    python scripts/import_leads.py 1 data/defi_leads.csv
fi

# 4. Generate drafts for all leads
echo "Generating drafts..."
curl -s -X POST http://localhost:8001/drafts/generate-bulk -d "client_id=1"

# 5. Show status
sleep 2
DRAFT_COUNT=$(sqlite3 data/leadservice.db "SELECT COUNT(*) FROM drafts;" 2>/dev/null || echo "0")
echo ""
echo "=== Ready! ==="
echo "Leads: $LEAD_COUNT"
echo "Drafts: $DRAFT_COUNT"
echo "Dashboard: http://localhost:8001/drafts"
