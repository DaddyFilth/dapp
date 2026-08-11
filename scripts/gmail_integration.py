import sqlite3, os, requests

DB = "../data/leadservice.db"

def find_lead_by_email(email):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id FROM leads WHERE contact_email LIKE ?", ('%' + email + '%',))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def process_email(lead_id, subject, body):
    response = requests.post('http://localhost:8001/replies/auto-reply', data={
        'lead_id': lead_id,
        'incoming_subject': subject,
        'incoming_body': body
    })
    return response.json()

if __name__ == "__main__":
    print("Gmail Integration Ready!")
    print("Usage:")
    print("1. Forward email to this script")
    print("2. Or manually call process_email(lead_id, subject, body)")
    print("")
    print("Example:")
    print("result = process_email(1, 'Re: Partnership', 'I am interested')")
    print("print(result['reply'])")
