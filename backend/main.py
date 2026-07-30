from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import sqlite3, os, json, asyncio, httpx
from datetime import datetime

app = FastAPI()
DB = "data/leadservice.db"
NL = chr(10)

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executescript("""
    PRAGMA foreign_keys = ON;
    DROP TABLE IF EXISTS clients;
    DROP TABLE IF EXISTS leads;
    DROP TABLE IF EXISTS drafts;
    DROP TABLE IF EXISTS replies;
    DROP TABLE IF EXISTS meetings;
    CREATE TABLE clients(id INTEGER PRIMARY KEY, name TEXT, website TEXT, calendar_link TEXT, pricing_plan TEXT, stripe_customer_id TEXT);
    CREATE TABLE leads(id INTEGER PRIMARY KEY, client_id INTEGER, protocol TEXT, tvl REAL, chains TEXT, category TEXT, score INTEGER, contact_email TEXT, contact_name TEXT, status TEXT DEFAULT 'new');
    CREATE TABLE drafts(id INTEGER PRIMARY KEY, lead_id INTEGER, subject TEXT, body TEXT, status TEXT DEFAULT 'draft', created_at TEXT, approved_at TEXT);
    CREATE TABLE replies(id INTEGER PRIMARY KEY, lead_id INTEGER, direction TEXT, subject TEXT, body TEXT, category TEXT, created_at TEXT);
    CREATE TABLE meetings(id INTEGER PRIMARY KEY, lead_id INTEGER, booked_at TEXT, meeting_time TEXT, status TEXT DEFAULT 'booked');
    """)
    conn.commit()
    conn.close()

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
async def root():
    return HTMLResponse("""<!doctype html><html><head><title>Lead Service</title><script src="https://cdn.tailwindcss.com"></script></head><body class="p-8 bg-gray-50"><h1 class="text-3xl font-bold mb-6">Lead Service Dashboard</h1><div class="grid grid-cols-3 gap-4 mb-6"><a href="/drafts" class="bg-blue-500 text-white p-6 rounded-lg hover:bg-blue-600"><h2 class="text-xl font-bold">Drafts</h2><p>Review and approve</p></a><a href="/meetings" class="bg-green-500 text-white p-6 rounded-lg hover:bg-green-600"><h2 class="text-xl font-bold">Meetings</h2><p>Booked calls</p></a><a href="/clients" class="bg-purple-500 text-white p-6 rounded-lg hover:bg-purple-600"><h2 class="text-xl font-bold">Clients</h2><p>Manage clients</p></a></div></body></html>""")

@app.get("/drafts")
async def drafts_page():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT d.id, d.lead_id, d.subject, d.body, d.status, l.protocol, l.tvl, l.contact_email FROM drafts d LEFT JOIN leads l ON d.lead_id = l.id ORDER BY d.created_at DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()
    
    drafts_html = ""
    for r in rows:
        draft_id, lead_id, subject, body, status, protocol, tvl, email = r
        status_color = "green" if status == "approved" else "yellow"
        drafts_html += f"""<div class="bg-white p-4 rounded shadow mb-4">
            <div class="flex justify-between items-center mb-2">
                <h3 class="font-bold text-lg">{subject}</h3>
                <span class="px-2 py-1 rounded bg-{status_color}-100 text-{status_color}-800 text-sm">{status}</span>
            </div>
            <p class="text-sm text-gray-600 mb-2">Protocol: {protocol} | TVL: ${int(tvl):,} | Contact: {email or 'N/A'}</p>
            <div class="bg-gray-50 p-3 rounded mb-3"><pre class="text-sm whitespace-pre-wrap">{body}</pre></div>
            <div class="flex gap-2">
                <button onclick="approveDraft({draft_id})" class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">Approve</button>
                <button onclick="rejectDraft({draft_id})" class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">Reject</button>
            </div>
        </div>"""
    
    return HTMLResponse(f"""<!doctype html><html><head><title>Drafts</title><script src="https://cdn.tailwindcss.com"></script></head><body class="p-8 bg-gray-50"><a href="/" class="text-blue-600 mb-4">&larr; Back</a><h1 class="text-3xl font-bold mb-6">Email Drafts</h1>{drafts_html}<script>
async function approveDraft(id) {{
    const r = await fetch('/drafts/approve', {{method: 'POST', headers: {{'Content-Type': 'application/x-www-form-urlencoded'}}, body: `draft_id=${{id}}`}});
    if (r.ok) location.reload();
}}
async function rejectDraft(id) {{
    alert('Draft ' + id + ' rejected (implement delete endpoint)');
}}
</script></body></html>""")

@app.get("/drafts-api")
async def list_drafts():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, lead_id, subject, body, status, created_at, approved_at FROM drafts ORDER BY created_at DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()
    return JSONResponse([{"id": r[0], "lead_id": r[1], "subject": r[2], "body": r[3], "status": r[4]} for r in rows])

@app.post("/drafts/generate")
async def generate_draft(lead_id: int = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT protocol, tvl, chains, contact_name FROM leads WHERE id=?", (lead_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Lead not found")
    protocol, tvl, chains, contact_name = row
    subject = "Partnership idea for " + str(protocol)
    contact = contact_name if contact_name else "there"
    tvl_fmt = f"{int(tvl):,}"
    body = "Hi " + contact + "," + NL + NL + "Congrats on " + str(protocol) + " (TVL $" + tvl_fmt + " on " + chains + "). I help DeFi protocols secure institutional partnerships." + NL + NL + "Open to a short chat?" + NL + NL + "Best," + NL + "Your Name"
    c.execute("INSERT INTO drafts (lead_id, subject, body, status, created_at) VALUES (?,?,?,?,?)", (lead_id, subject, body, "draft", datetime.utcnow().isoformat()))
    conn.commit()
    draft_id = c.lastrowid
    conn.close()
    return {"draft_id": draft_id}

@app.post("/drafts/approve")
async def approve_draft(draft_id: int = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE drafts SET status='approved', approved_at=? WHERE id=?", (datetime.utcnow().isoformat(), draft_id))
    conn.commit()
    conn.close()
    return {"status": "approved"}

@app.post("/drafts/generate-bulk")
async def generate_bulk_drafts(client_id: int = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, protocol, tvl, chains, contact_name FROM leads WHERE client_id=?", (client_id,))
    leads = c.fetchall()
    draft_ids = []
    for lead in leads:
        lead_id, protocol, tvl, chains, contact_name = lead
        subject = "Partnership idea for " + str(protocol)
        contact = contact_name if contact_name else "there"
        tvl_fmt = f"{int(tvl):,}"
        body = "Hi " + contact + "," + NL + NL + "Congrats on " + str(protocol) + " (TVL $" + tvl_fmt + " on " + chains + "). I help DeFi protocols secure institutional partnerships." + NL + NL + "Open to a short chat?" + NL + NL + "Best," + NL + "Your Name"
        c.execute("INSERT INTO drafts (lead_id, subject, body, status, created_at) VALUES (?,?,?,?,?)", (lead_id, subject, body, "draft", datetime.utcnow().isoformat()))
        draft_ids.append(c.lastrowid)
    conn.commit()
    conn.close()
    return {"drafts_created": len(draft_ids)}

@app.get("/clients")
async def list_clients():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM clients")
    rows = c.fetchall()
    conn.close()
    return JSONResponse([{"id": r[0], "name": r[1]} for r in rows])

@app.post("/clients")
async def create_client(name: str = Form(...), website: str = Form(...), calendar_link: str = Form(...), pricing_plan: str = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO clients (name, website, calendar_link, pricing_plan) VALUES (?,?,?,?)", (name, website, calendar_link, pricing_plan))
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return {"id": cid, "name": name}

@app.get("/meetings")
async def list_meetings():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM meetings ORDER BY booked_at DESC")
    rows = c.fetchall()
    conn.close()
    return JSONResponse([{"id": r[0], "lead_id": r[1], "meeting_time": r[3]} for r in rows])

@app.post("/meetings")
async def create_meeting(lead_id: int = Form(...), meeting_time: str = Form(...)):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO meetings (lead_id, booked_at, meeting_time) VALUES (?,?,?)", (lead_id, datetime.utcnow().isoformat(), meeting_time))
    conn.commit()
    mid = c.lastrowid
    conn.close()
    return {"meeting_id": mid}

@app.post("/billing/charge")
async def charge_for_meeting(amount_cents: int = Form(...), customer_email: str = Form(...), description: str = Form(...)):
    return {"status": "placeholder", "amount": amount_cents, "email": customer_email}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
