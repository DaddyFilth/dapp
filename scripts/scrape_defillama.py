import requests, csv, os

def scrape_defillama(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get top protocols from DefiLlama
    url = "https://api.llama.fi/protocols"
    response = requests.get(url, timeout=30)
    protocols = response.json()
    
    # Filter and sort by TVL
    top_protocols = []
    for p in protocols:
        tvl = p.get('tvl', 0)
        if tvl is None:
            tvl = 0
        if tvl > 1000000:  # Min $1M TVL
            top_protocols.append((p, tvl))
    
    # Sort by TVL descending
    top_protocols.sort(key=lambda x: x[1], reverse=True)
    top_protocols = top_protocols[:100]  # Top 100
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['protocol', 'tvl', 'chains', 'category', 'contact_email', 'contact_name'])
        
        for p, tvl in top_protocols:
            name = p.get('name', 'Unknown')
            chains = p.get('chains', [])
            if isinstance(chains, list) and len(chains) > 0:
                chains = '|'.join(str(c) for c in chains[:3])
            else:
                chains = 'Unknown'
            category = p.get('category', 'other')
            
            writer.writerow([name, int(tvl), chains, category, '', ''])
    
    print(f"Scraped {len(top_protocols)} protocols to {output_path}")
    return len(top_protocols)

if __name__ == "__main__":
    scrape_defillama("data/defi_leads.csv")
