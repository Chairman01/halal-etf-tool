from database import get_db_connection

def setup_database():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
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
        
        conn.commit()
        print("✅ Database tables created successfully!")
        
        # Verify tables exist
        cur.execute("SHOW TABLES")
        tables = cur.fetchall()
        print("\nExisting tables:")
        for table in tables:
            print(f"- {table[0]}")
            
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    setup_database() 