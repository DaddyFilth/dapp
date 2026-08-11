def get_reply_template(category, protocol, contact, tvl_fmt):
    if category == "hot_lead":
        return "Hi " + contact + ",Great! Book demo: [calendly-link]Best,[Your Name]"
    elif category == "pricing_inquiry":
        return "Hi " + contact + ",Pricing: Starter $500/mo, Pro $1500/mo (recommended for " + protocol + "), Enterprise custom.Best,[Your Name]"
    elif category == "feature_question":
        return "Hi " + contact + ",This answers user questions 24/7, reduces support tickets 40-60%, integrates in 1-2 days. Demo: [link]Best,[Your Name]"
    elif category == "not_interested":
        return "Hi " + contact + ",No problem! Removing you from our list.Best,[Your Name]"
    else:
        return "Hi " + contact + ",Thanks! I'll get back to you within 24 hours.Best,[Your Name]"
