import stripe, os
from datetime import datetime

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_KEY_HERE")

def create_payment_intent(amount_cents: int, customer_email: str, description: str):
    try:
        pi = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            payment_method_types=["card"],
            description=description,
            receipt_email=customer_email,
            metadata={"source": "lead_service"}
        )
        return {"status": "success", "client_secret": pi.client_secret, "payment_intent_id": pi.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def create_invoice_item(customer_id: str, amount_cents: int, description: str):
    try:
        item = stripe.InvoiceItem.create(
            customer=customer_id,
            amount=amount_cents,
            currency="usd",
            description=description
        )
        return {"status": "success", "invoice_item_id": item.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def finalize_and_send_invoice(customer_id: str):
    try:
        invoice = stripe.Invoice.create(
            customer=customer_id,
            auto_advance=True
        )
        return {"status": "success", "invoice_id": invoice.id, "invoice_url": invoice.hosted_invoice_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Test
    result = create_payment_intent(50000, "test@example.com", "Test charge - $500")
    print(result)
