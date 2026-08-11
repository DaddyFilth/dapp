import sqlite3, csv, sys
from datetime import datetime

DB = "data/leadservice.db"

def generate_report(client_id: int, output_path: str):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM leads WHERE client_id=?", (client_id,))
    total_leads = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM drafts d JOIN leads l ON d.lead_id = l.id WHERE l.client_id=?", (client_id,))
    total_drafts = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM drafts d JOIN leads l ON d.lead_id = l.id WHERE l.client_id=? AND d.status='approved'", (client_id,))
    approved_drafts = c.fetchone()[0]
    
    conn.close()
    
    report = f"""
# Client Report - Client ID: {client_id}
Generated: {datetime.now().isoformat()}

## Summary
- Total Leads: {total_leads}
- Total Drafts: {total_drafts}
- Approved Drafts: {approved_drafts}
- Approval Rate: {(approved_drafts/total_drafts*100) if total_drafts > 0 else 0:.1f}%

## Next Steps
1. Review approved drafts
2. Send via ESP
3. Track replies
4. Book meetings
"""
    
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"Report saved to {output_path}")
    return report

if __name__ == "__main__":
    client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    generate_report(client_id, f"output/client_{client_id}_report.md")
