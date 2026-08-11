from flask import Flask, render_template_string, jsonify, request, redirect
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('../data/leadservice.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    conn = get_db()
    total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    total_drafts = conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]
    approved = conn.execute("SELECT COUNT(*) FROM drafts WHERE status='approved'").fetchone()[0]
    total_meetings = conn.execute("SELECT COUNT(*) FROM meetings").fetchone()[0]
    conn.close()
    rows = ''
    html = DASH.replace('LEADS', str(total_leads)).replace('DRAFTS', str(total_drafts)).replace('APPROVED', str(approved)).replace('MEETINGS', str(total_meetings)).replace('MATCHES', rows)
    return html

@app.route('/leads')
def leads():
    conn = get_db()
    leads = conn.execute("SELECT * FROM leads ORDER BY CAST(tvl AS REAL) DESC").fetchall()
    total = len(leads)
    conn.close()
    rows = ''
    for l in leads:
        rows += '<tr><td><b>' + l['protocol'] + '</b></td><td>' + str(l['category']) + '</td><td>$' + str(round(float(str(l['tvl']) if l['tvl'] else 0)/1e6, 1)) + 'M</td><td>' + str(l['chains']) + '</td><td>' + str(l['contact_name'] or '-') + '</td></tr>'
    return LEADS.replace('TOTAL', str(total)).replace('ROWS', rows)

@app.route('/drafts')
def drafts():
    conn = get_db()
    drafts = conn.execute("SELECT * FROM drafts ORDER BY id DESC").fetchall()
    total = len(drafts)
    approved = len([d for d in drafts if d['status'] == 'approved'])
    pending = len([d for d in drafts if d['status'] == 'draft'])
    sent = len([d for d in drafts if d['status'] == 'sent'])
    conn.close()
    rows = ''
    for d in drafts:
        st = d['status'] or 'draft'
        rows += '<tr><td><b>' + str(d['lead_name']) + '</b></td><td>' + str(d['subject']) + '</td><td><span class="status status-' + st + '">' + st.upper() + '</span></td><td class="preview">' + str(d['body'] or '')[:60] + '...</td><td class="actions"><a href="/drafts/' + str(d['id']) + '/view" class="btn btn-view">View</a> <button class="btn btn-approve" onclick="approve(' + str(d['id']) + ')">OK</button> <button class="btn btn-reject" onclick="reject(' + str(d['id']) + ')">X</button></td></tr>'
    return DRAFTS.replace('TOTAL', str(total)).replace('APPROVED', str(approved)).replace('PENDING', str(pending)).replace('SENT', str(sent)).replace('ROWS', rows)

@app.route('/drafts/<int:id>/view')
def view_draft(id):
    conn = get_db()
    draft = conn.execute("SELECT * FROM drafts WHERE id = ?", (id,)).fetchone()
    conn.close()
    if not draft:
        return "Not found", 404
    html = VIEW.replace('PROTO', str(draft['lead_name'])).replace('STAT', str(draft['status'] or 'draft').upper()).replace('SUBJ', str(draft['subject'])).replace('BODY', str(draft['body'] or '')).replace('ID', str(draft['id']))
    return html

@app.route('/drafts/<int:id>/approve', methods=['POST'])
def approve_draft(id):
    conn = get_db()
    conn.execute("UPDATE drafts SET status = 'approved' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/drafts/<int:id>/send', methods=['POST'])
def send_draft(id):
    conn = get_db()
    conn.execute("UPDATE drafts SET status = 'sent' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/drafts/<int:id>/reject', methods=['POST'])
def reject_draft(id):
    conn = get_db()
    conn.execute("DELETE FROM drafts WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

DASH = """<!DOCTYPE html><html><head><title>Dashboard</title><style>body{font-family:Arial;padding:20px;background:#f5f5f5}.container{max-width:1400px;margin:0 auto}h1{color:#333;margin-bottom:20px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:20px}.stat{background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}.stat h3{color:#666;font-size:14px;margin-bottom:5px}.stat .value{font-size:32px;font-weight:bold;color:#2563eb}.section{background:#fff;padding:20px;border-radius:8px;margin-bottom:20px}.nav{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}.nav a{padding:10px 20px;background:#fff;border-radius:8px;text-decoration:none;color:#333}.nav a.active{background:#2563eb;color:#fff}table{width:100%}th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}th{background:#2563eb;color:#fff}tr:hover{background:#f9fafb}.score{padding:4px 8px;border-radius:4px;font-size:12px;font-weight:600}.score-90{background:#dcfce7;color:#16a34a}.score-70{background:#fef3c7;color:#d97706}.btn{padding:6px 12px;border-radius:4px;text-decoration:none;font-size:13px;cursor:pointer;border:none;margin:2px;background:#2563eb;color:#fff}</style></head><body><div class="container"><h1>LeadService Dashboard</h1><div class="nav"><a href="/dashboard" class="active">Dashboard</a><a href="/leads">Leads</a><a href="/drafts">Drafts</a><a href="/ai-matches">AI Matches</a><a href="/meetings">Meetings</a></div><div class="stats"><div class="stat"><h3>Total Leads</h3><div class="value">LEADS</div></div><div class="stat"><h3>Drafts</h3><div class="value">DRAFTS</div></div><div class="stat"><h3>Approved</h3><div class="value">APPROVED</div></div><div class="stat"><h3>Meetings</h3><div class="value">MEETINGS</div></div></div><div class="section"><h2>Top AI Matches</h2><table><thead><tr><th>Score</th><th>Protocol 1</th><th>Protocol 2</th><th>Reasons</th><th>Action</th></tr></thead><tbody>MATCHES</tbody></table></div></div></body></html>"""

LEADS = """<!DOCTYPE html><html><head><title>Leads</title><style>body{font-family:Arial;padding:20px;background:#f5f5f5}.container{max-width:1400px;margin:0 auto}h1{color:#333}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:20px 0}.stat{background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}.stat h3{color:#666;font-size:14px;margin-bottom:5px}.stat .value{font-size:28px;font-weight:bold;color:#2563eb}table{width:100%;background:#fff;border-radius:8px;overflow:hidden}th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}th{background:#2563eb;color:#fff}tr:hover{background:#f9fafb}.nav{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}.nav a{padding:10px 20px;background:#fff;border-radius:8px;text-decoration:none;color:#333}.nav a.active{background:#2563eb;color:#fff}</style></head><body><div class="container"><h1>Leads (TOTAL)</h1><div class="nav"><a href="/dashboard">Dashboard</a><a href="/leads" class="active">Leads</a><a href="/drafts">Drafts</a><a href="/ai-matches">AI Matches</a><a href="/meetings">Meetings</a></div><div class="stats"><div class="stat"><h3>Total Leads</h3><div class="value">TOTAL</div></div></div><table><thead><tr><th>Protocol</th><th>Category</th><th>TVL</th><th>Chains</th><th>Contact</th></tr></thead><tbody>ROWS</tbody></table></div></body></html>"""

DRAFTS = """<!DOCTYPE html><html><head><title>Drafts</title><style>body{font-family:Arial;padding:20px;background:#f5f5f5}.container{max-width:1400px;margin:0 auto}h1{color:#333}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:20px 0}.stat{background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}.stat h3{color:#666;font-size:14px;margin-bottom:5px}.stat .value{font-size:28px;font-weight:bold;color:#2563eb}table{width:100%;background:#fff;border-radius:8px;overflow:hidden}th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}th{background:#2563eb;color:#fff}tr:hover{background:#f9fafb}.nav{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}.nav a{padding:10px 20px;background:#fff;border-radius:8px;text-decoration:none;color:#333}.nav a.active{background:#2563eb;color:#fff}.status{padding:4px 8px;border-radius:4px;font-size:12px;font-weight:600}.status-draft{background:#e0e7ff;color:#4f46e5}.status-approved{background:#dcfce7;color:#16a34a}.status-sent{background:#dbeafe;color:#2563eb}.btn{padding:6px 12px;border-radius:4px;text-decoration:none;font-size:13px;cursor:pointer;border:none;margin:2px}.btn-view{background:#f59e0b;color:#fff}.btn-approve{background:#16a34a;color:#fff}.btn-reject{background:#dc2626;color:#fff}.actions{display:flex;gap:5px}.preview{color:#666;font-size:13px}</style></head><body><div class="container"><h1>Email Drafts</h1><div class="nav"><a href="/dashboard">Dashboard</a><a href="/leads">Leads</a><a href="/drafts" class="active">Drafts</a><a href="/ai-matches">AI Matches</a><a href="/meetings">Meetings</a></div><div class="stats"><div class="stat"><h3>Total Drafts</h3><div class="value">TOTAL</div></div><div class="stat"><h3>Approved</h3><div class="value">APPROVED</div></div><div class="stat"><h3>Pending</h3><div class="value">PENDING</div></div><div class="stat"><h3>Sent</h3><div class="value">SENT</div></div></div><table><thead><tr><th>Protocol</th><th>Subject</th><th>Status</th><th>Preview</th><th>Actions</th></tr></thead><tbody>ROWS</tbody></table></div><script>function approve(id){fetch('/drafts/'+id+'/approve',{method:'POST'}).then(()=>location.reload());}function send(id){fetch('/drafts/'+id+'/send',{method:'POST'}).then(()=>location.reload());}function reject(id){fetch('/drafts/'+id+'/reject',{method:'POST'}).then(()=>location.reload());}</script></body></html>"""

VIEW = """<!DOCTYPE html><html><head><title>View Draft</title><style>body{font-family:Arial;padding:20px;background:#f5f5f5}.container{max-width:800px;margin:0 auto;background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);padding:30px}h1{color:#333;margin-bottom:10px}.meta{color:#666;font-size:14px;margin-bottom:20px;padding-bottom:20px;border-bottom:2px solid #eee}.subject{font-size:22px;color:#2563eb;margin:20px 0 15px}.body{font-size:16px;line-height:1.8;color:#333;white-space:pre-wrap;background:#f8fafc;padding:25px;border-radius:8px;border:1px solid #e2e8f0}.actions{margin-top:25px;display:flex;gap:10px}.btn{padding:12px 24px;border-radius:4px;text-decoration:none;font-size:14px;cursor:pointer;border:none}.btn-back{background:#64748b;color:#fff}.btn-approve{background:#16a34a;color:#fff}.btn-send{background:#2563eb;color:#fff}.btn-reject{background:#dc2626;color:#fff}</style></head><body><div class="container"><h1>Email Draft</h1><div class="meta"><b>Protocol:</b> PROTO | <b>Status:</b> STAT</div><div class="subject">SUBJ</div><div class="body">BODY</div><div class="actions"><a href="/drafts" class="btn btn-back">Back</a><button class="btn btn-approve" onclick="approve(ID)">Approve</button><button class="btn btn-send" onclick="send(ID)">Send</button><button class="btn btn-reject" onclick="reject(ID)">Reject</button></div></div><script>function approve(id){fetch('/drafts/'+id+'/approve',{method:'POST'}).then(()=>location.href='/drafts');}function send(id){fetch('/drafts/'+id+'/send',{method:'POST'}).then(()=>location.href='/drafts');}function reject(id){fetch('/drafts/'+id+'/reject',{method:'POST'}).then(()=>location.href='/drafts');}</script></body></html>"""

if __name__ == '__main__':
    print("LeadService: http://localhost:8001")
    app.run(host='0.0.0.0', port=8001, debug=False)
