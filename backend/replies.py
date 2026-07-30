def classify_reply(body):
    b = body.lower()
    if "unsubscribe" in b or "opt-out" in b:
        return "unsubscribe"
    if "interested" in b or "yes" in b or "book" in b or "meeting" in b:
        return "interested"
    if "out of office" in b or "ooo" in b:
        return "ooo"
    return "other"
