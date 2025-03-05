from database import test_connection, init_db

if test_connection():
    print("Database connection successful!")
else:
    print("Database connection failed!")

if __name__ == "__main__":
    init_db() 