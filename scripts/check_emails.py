import requests, sqlite3, time

DB = "data/leadservice.db"

def check_manual_replies():
    """Check for new replies manually logged"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Get incoming replies that need response
    c.execute("""
        SELECT r.id, r.lead_id, r.subject, r.body, l.protocol, l.contact_email
        FROM replies r
        LEFT JOIN leads l ON r.lead_id = l.id
        WHERE r.direction = 'incoming' AND r.category = 'needs_reply'
        ORDER BY r.created_at DESC
        LIMIT 10
    """)
    
    replies = c.fetchall()
    conn.close()
    
    for reply in replies:
        reply_id, lead_id, subject, body, protocol, email = reply
        
        print(f"
Processing reply from {protocol}...")
        
        # Call AI
        response = requests.post('http://localhost:8001/replies/auto-reply', data={
            'lead_id': lead_id,
            'incoming_subject': subject,
            'incoming_body': body
        })
        
        result = response.json()
        print(f"AI Reply: {result['reply'][:100]}...")
        
        # Log the AI reply
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO replies (lead_id, direction, subject, body, category, created_at)
            VALUES (?, 'outgoing', ?, ?, 'auto', datetime('now'))
        """, (lead_id, 'Re: ' + subject, result['reply']))
        conn.commit()
        conn.close()
        
        print("Reply logged! Send manually via Gmail.")

if __name__ == "__main__":
    print("Checking for new replies...")
    check_manual_replies()
