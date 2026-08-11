import sqlite3
import json

def get_db():
    conn = sqlite3.connect('../data/leadservice.db')
    conn.row_factory = sqlite3.Row
    return conn

def analyze_compatibility(lead1, lead2):
    """AI analysis of compatibility between two protocols"""
    score = 0
    reasons = []
    
    # TVL compatibility (similar size = better partnership)
    tvl1 = float(str(lead1['tvl'] or 0))
    tvl2 = float(str(lead2['tvl'] or 0))
    tvl_ratio = min(tvl1, tvl2) / max(tvl1, tvl2) if max(tvl1, tvl2) > 0 else 0
    if tvl_ratio > 0.5:
        score += 25
        reasons.append("Similar TVL size")
    
    # Category complementarity (different categories = better)
    cat1 = lead1['category']
    cat2 = lead2['category']
    if cat1 != cat2:
        score += 30
        reasons.append(f"Complementary: {cat1} + {cat2}")
    else:
        score += 10
        reasons.append(f"Same category: {cat1}")
    
    # Chain overlap
    chains1 = set(str(lead1['chains']).split('|'))
    chains2 = set(str(lead2['chains']).split('|'))
    overlap = chains1.intersection(chains2)
    if overlap:
        score += 20
        reasons.append(f"Shared chains: {', '.join(overlap)}")
    
    # Volume synergy
    vol1 = float(str(lead1.get('volume_24h', 0)) or 0)
    vol2 = float(str(lead2.get('volume_24h', 0)) or 0)
    if vol1 > 0 and vol2 > 0:
        score += 15
        reasons.append("Both have trading volume")
    
    # Contact availability
    if lead1.get('contact_email') and lead2.get('contact_email'):
        score += 10
        reasons.append("Both have contact info")
    
    return min(100, score), reasons

def find_best_matches():
    """Find best meeting opportunities"""
    conn = get_db()
    leads = conn.execute("SELECT * FROM leads").fetchall()
    
    matches = []
    for i, lead1 in enumerate(leads):
        for lead2 in leads[i+1:]:
            score, reasons = analyze_compatibility(lead1, lead2)
            if score > 50:  # Only good matches
                match = {
                    'protocol1': lead1['protocol'],
                    'protocol2': lead2['protocol'],
                    'category1': lead1['category'],
                    'category2': lead2['category'],
                    'tvl1': float(str(lead1['tvl'] or 0)) / 1000000,
                    'tvl2': float(str(lead2['tvl'] or 0)) / 1000000,
                    'score': score,
                    'reasons': reasons,
                    'email1': lead1.get('contact_email', ''),
                    'email2': lead2.get('contact_email', '')
                }
                matches.append(match)
    
    # Sort by score
    matches.sort(key=lambda x: x['score'], reverse=True)
    conn.close()
    
    return matches[:50]  # Top 50 matches

if __name__ == '__main__':
    matches = find_best_matches()
    print(f"Found {len(matches)} potential matches")
    for m in matches[:5]:
        print(f"{m['protocol1']} <-> {m['protocol2']}: {m['score']}/100")
