import csv, sqlite3, os

DB = "data/leadservice.db"

def import_leads_from_csv(client_id: int, csv_path: str):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            c.execute("""
                INSERT INTO leads (client_id, protocol, tvl, chains, category, score, contact_email, contact_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_id,
                row.get('name', ''),
                float(row.get('tvl', 0)),
                row.get('chains', ''),
                row.get('category', ''),
                int(row.get('score', 0)),
                row.get('contact_email', ''),
                row.get('contact_name', '')
            ))
            count += 1
        
        conn.commit()
        conn.close()
        return count

if __name__ == "__main__":
    # Test import
    count = import_leads_from_csv(1, '../scrapers/output/defi_leads.csv')
    print(f"Imported {count} leads")
