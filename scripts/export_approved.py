import sqlite3, csv, sys

DB = "data/leadservice.db"

def export_approved(output_path="output/approved_emails.csv"):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT d.subject, d.body, l.protocol, l.tvl, l.contact_email, l.contact_name
        FROM drafts d
        LEFT JOIN leads l ON d.lead_id = l.id
        WHERE d.status = 'approved'
        ORDER BY d.approved_at DESC
    """)
    
    rows = c.fetchall()
    conn.close()
    
    import os
    os.makedirs("output", exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['subject', 'body', 'protocol', 'tvl', 'contact_email', 'contact_name'])
        writer.writerows(rows)
    
    print(f"Exported {len(rows)} approved emails to {output_path}")
    return len(rows)

if __name__ == "__main__":
    export_approved()
