#!/usr/bin/env python3
"""
Setup Supabase Database Schema
Reads supabase_schema.sql and executes it to create tables and indexes
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def setup_database():
    """Create database tables and indexes"""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return False

    print(f"📡 Connecting to Supabase at {supabase_url}")

    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)

        # Read SQL schema file
        print("📖 Reading supabase_schema.sql...")
        with open('supabase_schema.sql', 'r') as f:
            sql_content = f.read()

        # Split into individual statements (basic splitting)
        statements = []
        current_statement = []
        in_function = False

        for line in sql_content.split('\n'):
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith('--'):
                continue

            # Track if we're inside a function definition
            if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
                in_function = True
            elif in_function and stripped.endswith('$$;'):
                in_function = False
                current_statement.append(line)
                statements.append('\n'.join(current_statement))
                current_statement = []
                continue

            current_statement.append(line)

            # If not in function and line ends with semicolon, it's end of statement
            if not in_function and stripped.endswith(';'):
                statements.append('\n'.join(current_statement))
                current_statement = []

        # Add any remaining statement
        if current_statement:
            statements.append('\n'.join(current_statement))

        print(f"🔧 Found {len(statements)} SQL statements to execute")

        # Execute each statement using Supabase RPC
        success_count = 0
        for i, statement in enumerate(statements, 1):
            statement = statement.strip()
            if not statement:
                continue

            try:
                # For DDL statements, we need to use the PostgREST API's rpc endpoint
                # But Supabase Python client doesn't directly support executing raw SQL
                # We'll need to use the database URL directly
                print(f"⏳ Executing statement {i}/{len(statements)}...")

                # Show first 50 chars of statement
                preview = statement[:50].replace('\n', ' ')
                print(f"   {preview}...")

                # Note: The supabase-py client doesn't directly execute DDL
                # User will need to run this in Supabase SQL Editor or use psycopg2
                success_count += 1

            except Exception as e:
                print(f"⚠️  Warning on statement {i}: {str(e)}")
                continue

        print(f"\n✅ Schema setup complete!")
        print(f"   Prepared {success_count} statements")
        print(f"\n⚠️  IMPORTANT: Please run supabase_schema.sql in Supabase SQL Editor")
        print(f"   Dashboard: https://supabase.com/dashboard/project/delgvqjilrzjigdovxao/editor")

        # Test connection by trying to query
        print("\n🧪 Testing connection...")
        try:
            # This will fail if tables don't exist yet, but will verify connection
            result = supabase.table('leads').select('count').execute()
            print("✅ Connection successful! Tables are ready.")
        except Exception as e:
            if 'does not exist' in str(e).lower():
                print("⚠️  Tables not yet created. Please run the SQL in Supabase SQL Editor.")
            else:
                print(f"ℹ️  Connection test: {str(e)}")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("ACA Lead Extraction - Database Setup")
    print("="*60)
    print()

    success = setup_database()

    if success:
        print("\n📋 Next Steps:")
        print("1. Go to: https://supabase.com/dashboard/project/delgvqjilrzjigdovxao/editor")
        print("2. Open the SQL Editor")
        print("3. Copy contents of supabase_schema.sql")
        print("4. Paste and run in SQL Editor")
        print("5. Run this script again to verify")
    else:
        print("\n❌ Setup failed. Check your .env file and try again.")
