
import os
import psycopg
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
# Read database connection string from environment
database_url = os.getenv("DATABASE_URL")

# Connect to PostgreSQL
with psycopg.connect(database_url) as conn:

    # Create cursor for executing SQL
    with conn.cursor() as cursor:

        # Execute read-only SQL query
        cursor.execute(
            """
            SELECT id, user_query, source_used, created_at
            FROM audit_logs
            ORDER BY id DESC
            LIMIT 5
            """
        )

        # Fetch query results
        records = cursor.fetchall()

        # Display retrieved records
        for record in records:
            print(record)

print("PostgreSQL connection successful!")
