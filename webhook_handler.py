import stripe
import os
from dotenv import load_dotenv
from database import get_db_connection, update_subscription_status

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def handle_successful_payment(session):
    """Handle successful subscription payment"""
    print("\n=== Processing Webhook Payment ===")
    
    customer_email = session.get('customer_details', {}).get('email')
    customer_id = session.get('customer')
    
    print(f"Payment Email: {customer_email}")
    print(f"Customer ID: {customer_id}")
    
    # First try to find user by exact email match
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Check if any user exists with this email
        cur.execute('SELECT username, email FROM users WHERE email = %s', (customer_email,))
        user = cur.fetchone()
        
        if not user:
            print(f"⚠️ No user found with payment email: {customer_email}")
            # Store pending subscription in new table
            cur.execute('''
                INSERT INTO pending_subscriptions 
                (email, stripe_customer_id, payment_date) 
                VALUES (%s, %s, NOW())
            ''', (customer_email, customer_id))
            conn.commit()
            print("✅ Stored as pending subscription")
            return
            
        # Update subscription for matched user
        success = update_subscription_status(
            email=user['email'],
            stripe_customer_id=customer_id
        )
        
        if success:
            print(f"✅ Updated subscription for {user['email']}")
        else:
            print(f"❌ Failed to update subscription for {user['email']}")
            
    except Exception as e:
        print(f"❌ Error in handle_successful_payment: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

def handle_webhook_event(event):
    """Handle different types of webhook events"""
    try:
        print(f"\n=== Received Webhook Event: {event['type']} ===")
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_successful_payment(session)
        elif event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            print(f"New subscription created: {subscription['id']}")
            print(f"Customer: {subscription['customer']}")
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            print(f"Payment succeeded for invoice: {invoice['id']}")
            print(f"Customer: {invoice['customer']}")
            
    except Exception as e:
        print(f"Error handling webhook: {e}")
        raise e 