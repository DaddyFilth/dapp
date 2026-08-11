import sqlite3, sys, os
from datetime import datetime

DB = "data/leadservice.db"

class AIEmailBot:
    def __init__(self):
        self.conn = sqlite3.connect(DB)
        self.c = self.conn.cursor()
    
    def categorize_incoming(self, subject: str, body: str) -> dict:
        text = (subject + " " + body).lower()
        
        categories = {
            "hot_lead": {
                "keywords": ["interested", "yes", "sure", "let's talk", "meeting", "demo", "call", "schedule"],
                "action": "send_calendly",
                "priority": "high"
            },
            "pricing_inquiry": {
                "keywords": ["price", "cost", "how much", "pricing", "budget", "expensive", "cheap"],
                "action": "send_pricing",
                "priority": "medium"
            },
            "feature_question": {
                "keywords": ["how does", "what is", "explain", "feature", "work", "integration"],
                "action": "send_info",
                "priority": "medium"
            },
            "not_interested": {
                "keywords": ["no thanks", "not interested", "unsubscribe", "stop", "remove"],
                "action": "mark_unsubscribe",
                "priority": "low"
            },
            "out_of_office": {
                "keywords": ["ooo", "out of office", "vacation", "away", "returning"],
                "action": "follow_up_later",
                "priority": "low"
            }
        }
        
        best_match = "other"
        best_score = 0
        
        for cat, config in categories.items():
            score = sum(1 for kw in config["keywords"] if kw in text)
            if score > best_score:
                best_score = score
                best_match = cat
        
        return {
            "category": best_match,
            "confidence": best_score,
            "action": categories.get(best_match, {}).get("action", "manual_review"),
            "priority": categories.get(best_match, {}).get("priority", "medium")
        }
    
    def generate_reply(self, lead_id: int, category: str, incoming_subject: str, incoming_body: str) -> str:
        self.c.execute("SELECT protocol, tvl, contact_name, contact_email FROM leads WHERE id=?", (lead_id,))
        row = self.c.fetchone()
        if not row:
            return "Lead not found"
        
        protocol, tvl, contact_name, contact_email = row
        tvl_fmt = f"{int(tvl):,}"
        contact = contact_name if contact_name else "there"
        
        replies = {
            "hot_lead": f"Hi {contact},

Great! I'd love to show you how our AI chat can help {protocol} users.

Book a demo here: [your-calendly-link]

Or I can send you a personalized demo video first.

Best,
[Your Name]",

            "pricing_inquiry": f"Hi {contact},

Thanks for asking! Here's our pricing for {protocol}:

- Starter: $500/mo (1,000 conversations)
- Pro: $1,500/mo (10,000 conversations) <- Recommended for you
- Enterprise: Custom pricing

For {protocol} (${tvl_fmt} TVL), Pro gives you the best value.

Want to see a demo first?

Best,
[Your Name]",

            "feature_question": f"Hi {contact},

Great question! Our AI chat for {protocol} can:

- Answer user questions 24/7
- Explain staking, bridging, swapping in simple terms
- Reduce support tickets by 40-60%
- Integrate in 1-2 days (widget or API)

Here's a live demo: [demo-link]

Want to see how it works for {protocol} specifically?

Best,
[Your Name]",

            "not_interested": f"Hi {contact},

No problem! I'll remove you from our list.

If you ever need AI chat for {protocol} users in the future, feel free to reach out.

Best,
[Your Name]",

            "out_of_office": f"Hi {contact},

Thanks for the heads up! I'll follow up when you're back.

Enjoy your time off!

Best,
[Your Name]",

            "other": f"Hi {contact},

Thanks for your message! I'll get back to you within 24 hours with a detailed response.

Best,
[Your Name]"
        }
        
        return replies.get(category, replies["other"])
    
    def process_incoming_email(self, lead_id: int, subject: str, body: str):
        analysis = self.categorize_incoming(subject, body)
        reply = self.generate_reply(lead_id, analysis["category"], subject, body)
        
        self.c.execute("""
            INSERT INTO replies (lead_id, direction, subject, body, category, created_at)
            VALUES (?, 'outgoing', ?, ?, ?, ?)
        """, (lead_id, "Re: " + subject, reply, analysis["category"], datetime.utcnow().isoformat()))
        self.conn.commit()
        
        return {
            "category": analysis["category"],
            "priority": analysis["priority"],
            "reply": reply,
            "action": analysis["action"]
        }
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    bot = AIEmailBot()
    
    lead_id = 1
    subject = "Re: AI Chat for Uniswap users"
    body = "I'm interested in learning more. How does it work?"
    
    result = bot.process_incoming_email(lead_id, subject, body)
    
    print("Category:", result["category"])
    print("Priority:", result["priority"])
    print("
Suggested Reply:")
    print(result["reply"])
    
    bot.close()
