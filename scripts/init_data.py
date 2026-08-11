import sqlite3
import os

os.makedirs('data', exist_ok=True)
conn = sqlite3.connect('data/leadservice.db')

# Generate drafts if needed
leads = conn.execute("SELECT * FROM leads").fetchall()
draft_count = conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]

if draft_count == 0 and leads:
    print("Generating " + str(len(leads)) + " drafts...")
    for lead in leads:
        subject = "Partnership with " + lead['protocol']
        body = "Hi " + lead['protocol'] + " team,

Impressed by your TVL.

Best,
Partnership Team"
        conn.execute(
            "INSERT INTO drafts (lead_name, subject, body) VALUES (?, ?, ?)",
            (lead['protocol'], subject, body)
        )
    conn.commit()
    print("Done!")
else:
    print("Drafts exist: " + str(draft_count))

conn.close()
