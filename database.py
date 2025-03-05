import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import bcrypt
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# At the top, after load_dotenv()
print("Environment variables loaded:")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")

# After load_dotenv()
print("\nEnvironment Check:")
print("-" * 50)
print(f"DB_USER: '{os.getenv('DB_USER')}'")
print(f"DB_HOST: '{os.getenv('DB_HOST')}'")
print(f"DB_NAME: '{os.getenv('DB_NAME')}'")
print(f"DB_PASSWORD length: {len(os.getenv('DB_PASSWORD', ''))} chars")

# Update DB_CONFIG with more explicit error handling
DB_CONFIG = {
    'host': os.getenv('DB_HOST') or 'localhost',
    'user': os.getenv('DB_USER') or 'halal_user',
    'password': os.getenv('DB_PASSWORD'),  # This must match what you set in MySQL
    'database': os.getenv('DB_NAME') or 'halal_etf_db'
}

print("\nConnection Config:")
print("-" * 50)
print(f"host: '{DB_CONFIG['host']}'")
print(f"user: '{DB_CONFIG['user']}'")
print(f"database: '{DB_CONFIG['database']}'")
print(f"password length: {len(DB_CONFIG['password'] or '')}")

def get_db_connection():
    try:
        # Print connection details (remove in production)
        print("Attempting to connect with settings:")
        print(f"Host: {os.getenv('DB_HOST', 'localhost')}")
        print(f"User: {os.getenv('DB_USER', 'halal_user')}")
        print(f"Database: {os.getenv('DB_NAME', 'halal_etf_db')}")
        
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'halal_user'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'halal_etf_db')
        )
        print("Connection successful!")
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise e

def init_db():
    """Initialize database and create tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Create users table if not exists
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
        
        # Create pending_subscriptions table if not exists
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
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def update_subscription_status(email, stripe_customer_id, status='active'):
    """Update user's subscription status"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Set subscription end date to 1 month from now
        end_date = datetime.now().replace(microsecond=0) + timedelta(days=30)
        
        cur.execute('''
            UPDATE users 
            SET stripe_customer_id = %s,
                subscription_status = %s,
                subscription_end_date = %s
            WHERE email = %s
        ''', (stripe_customer_id, status, end_date, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating subscription: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def create_user(email, username, password, name):
    conn = None
    cur = None
    try:
        print(f"Creating user: {username}")
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute(
            "SELECT 1 FROM users WHERE email = %s OR username = %s",
            (email, username)
        )
        if cur.fetchone():
            return False, "User already exists"
        
        # Create new user with default subscription status
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_password_hex = hashed_password.hex()
        
        cur.execute(
            """
            INSERT INTO users (
                email, username, password, name, 
                subscription_status, subscription_end_date
            )
            VALUES (%s, %s, %s, %s, 'active', DATE_ADD(NOW(), INTERVAL 30 DAY))
            """,
            (email, username, hashed_password_hex, name)
        )
        
        conn.commit()
        return True, "User created successfully"
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return False, str(e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def verify_user(username, password):
    conn = None
    cur = None
    try:
        print(f"\n=== Starting verification for username: {username} ===")
        conn = get_db_connection()
        if not conn:
            print("Failed to get database connection")
            return None
            
        cur = conn.cursor(dictionary=True)
        
        # Get user with simpler query
        query = "SELECT * FROM users WHERE username = %s"
        print(f"Executing query: {query} with username: {username}")
        cur.execute(query, (username,))
        
        user = cur.fetchone()
        if user:
            print("Found user record:")
            print(f"Username: {user['username']}")
            print(f"Name: {user['name']}")
            print(f"Password hash length: {len(user['password'])}")
            
            try:
                # Convert password to bytes
                password_bytes = password.encode('utf-8')
                print(f"Input password converted to bytes, length: {len(password_bytes)}")
                
                # Convert stored hex string back to bytes
                stored_hash = bytes.fromhex(user['password'])
                print(f"Stored hash converted from hex, length: {len(stored_hash)}")
                
                # Verify password
                is_valid = bcrypt.checkpw(password_bytes, stored_hash)
                print(f"Password verification result: {is_valid}")
                
                if is_valid:
                    print("Login successful!")
                    return user
                else:
                    print("Password verification failed")
                    return None
                    
            except Exception as e:
                print(f"Error during password verification: {str(e)}")
                print(f"Error type: {type(e)}")
                return None
        else:
            print(f"No user found with username: {username}")
            return None
            
    except Exception as e:
        print(f"Database error in verify_user: {str(e)}")
        print(f"Error type: {type(e)}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("=== Database connection closed ===\n")

def test_connection():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT VERSION()')
        version = cur.fetchone()
        print(f"Successfully connected to MySQL. Version: {version[0]}")
        return True
    except Error as e:
        print(f"Error connecting to database: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def verify_db_setup():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if we can query the database
        cur.execute("SELECT DATABASE()")
        db_name = cur.fetchone()[0]
        print(f"Connected to database: {db_name}")
        
        # Check users table structure
        cur.execute("DESCRIBE users")
        columns = cur.fetchall()
        print("Users table structure:")
        for column in columns:
            print(column)
        
        # Check for existing users
        cur.execute("SELECT username, email FROM users")
        users = cur.fetchall()
        print(f"Existing users: {users}")
        
        return True
    except Exception as e:
        print(f"Database verification failed: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close() 