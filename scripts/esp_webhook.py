from fastapi import FastAPI, Request
import requests, sqlite3

DB = "../data/leadservice.db"
app = FastAPI()

@app.post("/webhook/esp")
async def esp_webhook(request: Request):
    """Handle ESP webhook for new replies"""
    data = await request.json()
    
    # Extract email data from ESP
    lead_email = data.get('email', '')
    subject = data.get('subject', '')
    body = data.get('body', '')
    
    # Find lead by email
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id FROM leads WHERE contact_email LIKE ?", (f'%{lead_email}%',))
    row = c.fetchone()
    conn.close()
    
    if row:
        lead_id = row[0]
        
        # Call AI auto-reply
        response = requests.post('http://localhost:8001/replies/auto-reply', data={
            'lead_id': lead_id,
            'incoming_subject': subject,
            'incoming_body': body
        })
        
        result = response.json()
        
        # Return reply to ESP
        return {
            "status": "success",
            "category": result['category'],
            "reply": result['reply']
        }
    else:
        return {"status": "unknown_lead"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
