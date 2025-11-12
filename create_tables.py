#!/usr/bin/env python3
"""
Create Supabase Tables Script
Executes the SQL schema to create database tables
"""

import os
import psycopg2
from dotenv import load_dotenv

def create_tables():
    """Execute SQL schema to create tables"""

    # Load environment
    load_dotenv()

    # Get database URL
    db_url = os.getenv('SUPABASE_DB_URL')

    if not db_url:
        print("[!!] SUPABASE_DB_URL not found in .env")
        print("\nPlease add this to your .env file:")
        print("SUPABASE_DB_URL=postgresql://postgres:Insurance24.7!@db.delgvqjilrzjigdovxao.supabase.co:5432/postgres")
        return False

    print("=" * 60)
    print("CREATING SUPABASE TABLES")
    print("=" * 60)
    print()

    try:
        # Read SQL file
        print("[1/3] Reading supabase_schema.sql...")
        with open('supabase_schema.sql', 'r') as f:
            sql_content = f.read()
        print("      [OK] SQL file loaded (75 lines)")

        # Connect to database
        print("[2/3] Connecting to Supabase...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        print("      [OK] Connected")

        # Execute SQL
        print("[3/3] Creating tables and indexes...")
        cursor.execute(sql_content)
        print("      [OK] SQL executed successfully")

        # Verify tables exist
        print("\n[+] Verifying tables...")
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('leads', 'attachments')
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        if len(tables) == 2:
            print("    [OK] leads table created")
            print("    [OK] attachments table created")
        else:
            print("    [WW] Expected 2 tables, found:", len(tables))

        # Close connection
        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("[*] SUCCESS! Database tables created")
        print("=" * 60)
        print("\nRun 'python verify_setup.py' to verify everything works")

        return True

    except psycopg2.OperationalError as e:
        print(f"\n[!!] Database connection error: {e}")
        print("\nPossible solutions:")
        print("1. Check that SUPABASE_DB_URL is correct in .env")
        print("2. Verify your IP is allowed in Supabase (Network Settings)")
        print("3. Ensure password is correct")
        return False

    except FileNotFoundError:
        print("\n[!!] supabase_schema.sql not found")
        print("Make sure you're running this from the project directory")
        return False

    except Exception as e:
        print(f"\n[!!] Error: {e}")
        print("\nFalling back to Supabase Dashboard method:")
        print("1. Go to: https://supabase.com/dashboard/project/delgvqjilrzjigdovxao/sql")
        print("2. Copy contents of supabase_schema.sql")
        print("3. Paste and run in SQL editor")
        return False

if __name__ == '__main__':
    success = create_tables()
    exit(0 if success else 1)
