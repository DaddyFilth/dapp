def make_draft(protocol, tvl, chains, category, contact_name):
    subject = f"Partnership idea for {protocol}"
    body = f"Hi {contact_name or 'there'},

Congrats on {protocol} (TVL ${tvl:,.0f} on {chains}). I help DeFi protocols secure institutional partnerships and liquidity intros.

Would you be open to a short chat this week?

Best,
Your Name"
    return subject, body
