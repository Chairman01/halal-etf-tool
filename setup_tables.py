from database import get_db_connection

def setup_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                stripe_customer_id VARCHAR(255),
                subscription_status VARCHAR(50) DEFAULT 'inactive',
                subscription_end_date DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create pending_subscriptions table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pending_subscriptions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                stripe_customer_id VARCHAR(255) NOT NULL,
                payment_date DATETIME NOT NULL,
                claimed_by_user_id INT,
                claimed_date DATETIME,
                FOREIGN KEY (claimed_by_user_id) REFERENCES users(id)
            )
        ''')
        
        # Create newsletter_subscribers table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(100),
                subscribed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status ENUM('active', 'unsubscribed') DEFAULT 'active'
            )
        ''')
        
        conn.commit()
        print("✅ Tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    setup_tables() 