import sqlite3

conn = sqlite3.connect('data/leadservice.db')
leads = conn.execute("SELECT * FROM leads").fetchall()

print("Creating drafts for", len(leads), "leads...")

for lead in leads:
    protocol = lead['protocol']
    subject = "Partnership with " + protocol
    body = "Hi " + protocol + " team,

I've been following your protocol and am impressed by your TVL.

We'd love to explore a partnership opportunity.

Are you open to a brief call next week?

Best regards,
Partnership Team"
    
    conn.execute(
        "INSERT INTO drafts (lead_name, subject, body) VALUES (?, ?, ?)",
        (protocol, subject, body)
    )

conn.commit()
print("Created", len(leads), "drafts!")
conn.close()
