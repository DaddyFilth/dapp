import sqlite3, csv, sys

DB = "data/leadservice.db"

def import_leads(client_id: int, csv_path: str):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
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
            except Exception as e:
                print(f"Error: {e}")
                continue
        
        conn.commit()
        conn.close()
        return count

if __name__ == "__main__":
    client_id = int(sys.argv[1])
    csv_path = sys.argv[2]
    count = import_leads(client_id, csv_path)
    print(f"Imported {count} leads")
