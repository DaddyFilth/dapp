from flask import Flask
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('../data/leadservice.db')
    conn.row_factory = sqlite3.Row
    return conn

def analyze(lead1, lead2):
    score = 0
    reasons = []
    tvl1 = float(str(lead1['tvl']) if lead1['tvl'] else 0)
    tvl2 = float(str(lead2['tvl']) if lead2['tvl'] else 0)
    if min(tvl1, tvl2) / max(tvl1, tvl2) > 0.5 if max(tvl1, tvl2) > 0 else False:
        score += 25
        reasons.append("Similar TVL")
    if lead1['category'] != lead2['category']:
        score += 30
        reasons.append("Complementary")
    else:
        score += 10
    chains1 = set(str(lead1['chains']).split('|'))
    chains2 = set(str(lead2['chains']).split('|'))
    if chains1 & chains2:
        score += 20
        reasons.append("Shared chains")
    try:
        vol1 = float(str(lead1['volume_24h']) if lead1['volume_24h'] else 0)
        vol2 = float(str(lead2['volume_24h']) if lead2['volume_24h'] else 0)
        if vol1 > 0 and vol2 > 0:
            score += 15
            reasons.append("Both have volume")
    except:
        pass
    try:
        if lead1['contact_email'] and lead2['contact_email']:
            score += 10
            reasons.append("Both have contacts")
    except:
        pass
    return min(100, score), reasons

def find_matches():
    conn = get_db()
    leads = conn.execute("SELECT * FROM leads").fetchall()
    matches = []
    for i, l1 in enumerate(leads):
        for l2 in leads[i+1:]:
            score, reasons = analyze(l1, l2)
            if score > 50:
                matches.append({
                    'p1': l1['protocol'],
                    'p2': l2['protocol'],
                    'c1': l1['category'],
                    'c2': l2['category'],
                    'tvl1': float(str(l1['tvl']) if l1['tvl'] else 0) / 1e6,
                    'tvl2': float(str(l2['tvl']) if l2['tvl'] else 0) / 1e6,
                    'score': score,
                    'reasons': reasons
                })
    matches.sort(key=lambda x: x['score'], reverse=True)
    conn.close()
    return matches

@app.route('/')
def dashboard():
    matches = find_matches()
    top = matches[:10]
    s90 = len([m for m in matches if m['score'] >= 90])
    s70 = len([m for m in matches if m['score'] >= 70])
    avg = round(sum(m['score'] for m in matches) / len(matches), 1) if matches else 0
    
    rows = ''
    for m in top:
        sclass = 'score-90' if m['score']>=90 else 'score-70' if m['score']>=70 else 'score-50'
        rows += '<tr><td><span class="score ' + sclass + '">' + str(m['score']) + '</span></td><td><b>' + m['p1'] + '</b></td><td><b>' + m['p2'] + '</b></td><td>' + m['c1'] + ' + ' + m['c2'] + '</td><td>$' + str(round(m['tvl1'],1)) + 'M / $' + str(round(m['tvl2'],1)) + 'M</td><td class="reasons">' + ', '.join(m['reasons'][:2]) + '</td></tr>'
    
    html = '''<!DOCTYPE html><html><head><title>AI Matches</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial,sans-serif;padding:10px;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh}
.container{max-width:100%;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.2)}
header{background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;padding:15px}
h1{font-size:20px;margin-bottom:5px}
h2{font-size:14px;opacity:.9;font-weight:400}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;padding:15px;background:#f8fafc}
.stat{background:#fff;padding:10px;border-radius:6px;text-align:center}
.stat .label{color:#64748b;font-size:11px;margin-bottom:5px;text-transform:uppercase}
.stat .value{font-size:24px;font-weight:700;color:#2563eb}
.content{padding:10px}
h3{color:#1e293b;font-size:16px;margin-bottom:15px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#f1f5f9;color:#475569;padding:8px 5px;text-align:left;font-weight:600}
td{padding:8px 5px;border-bottom:1px solid #e2e8f0}
tr:hover{background:#f8fafb}
.score{padding:4px 8px;border-radius:12px;font-size:11px;font-weight:700;display:inline-block}
.score-90{background:#dcfce7;color:#16a34a}
.score-70{background:#fef3c7;color:#d97706}
.score-50{background:#e0e7ff;color:#4f46e5}
.reasons{color:#64748b;font-size:11px}
@media (max-width: 768px){
.stats{grid-template-columns:repeat(2,1fr)}
table{font-size:11px}
th,td{padding:6px 3px}
}
</style></head><body><div class="container"><header><h1>AI Partnership Matcher</h1><h2>Intelligent protocol matching</h2></header><div class="stats"><div class="stat"><div class="label">Total</div><div class="value">''' + str(len(matches)) + '''</div></div><div class="stat"><div class="label">90+</div><div class="value">''' + str(s90) + '''</div></div><div class="stat"><div class="label">70+</div><div class="value">''' + str(s70) + '''</div></div><div class="stat"><div class="label">Avg</div><div class="value">''' + str(avg) + '''</div></div></div><div class="content"><h3>Top 10 Matches</h3><table><thead><tr><th>Score</th><th>Protocol 1</th><th>Protocol 2</th><th>Cats</th><th>TVL</th><th>Reasons</th></tr></thead><tbody>''' + rows + '''</tbody></table></div></div></body></html>'''
    
    return html

if __name__ == '__main__':
    print("AI Dashboard: http://localhost:8002")
    app.run(host='0.0.0.0', port=8002, debug=False)
