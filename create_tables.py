#!/usr/bin/env python3
"""
Create Supabase Tables Script
Executes the SQL schema to create database tables
"""

import os
import socket
import ssl
from urllib.parse import parse_qsl, urlparse

import requests
from dotenv import load_dotenv
from pg8000.dbapi import DatabaseError, InterfaceError, connect


def build_connection_params(db_url: str):
    """Parse the database URL into pg8000-friendly connection params."""
    parsed = urlparse(db_url)

    if parsed.scheme not in ('postgresql', 'postgres'):
        raise ValueError("SUPABASE_DB_URL must start with postgresql:// or postgres://")

    if not parsed.hostname:
        raise ValueError("Missing host in SUPABASE_DB_URL")

    if not parsed.username or not parsed.password:
        raise ValueError("Database username/password missing from SUPABASE_DB_URL")

    dbname = parsed.path.lstrip('/') or 'postgres'
    port = parsed.port or 5432

    query_params = dict(parse_qsl(parsed.query)) if parsed.query else {}
    try:
        timeout = int(query_params.get('connect_timeout', 30))
    except ValueError:
        timeout = 30

    resolved_host = _resolve_hostaddr(parsed.hostname)

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False

    connect_kwargs = {
        'database': dbname,
        'user': parsed.username,
        'password': parsed.password,
        'host': resolved_host,
        'port': port,
        'timeout': timeout,
        'ssl_context': ssl_context,
    }

    return connect_kwargs, {'original_host': parsed.hostname, 'resolved_host': resolved_host}


def _resolve_hostaddr(host: str) -> str:
    """Resolve hostname to an IP address with fallbacks."""
    try:
        return _resolve_with_socket(host)
    except socket.gaierror:
        fallback = _resolve_with_doh(host)
        if fallback:
            return fallback
        raise RuntimeError(f"Unable to resolve {host}: DNS lookup failed in socket and DoH fallbacks")


def _resolve_with_socket(host: str) -> str:
    addr_info = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    ipv4 = next((info for info in addr_info if info[0] == socket.AF_INET), None)
    target = ipv4 or addr_info[0]
    return target[4][0]


def _resolve_with_doh(host: str) -> str | None:
    """Resolve via Google's DNS-over-HTTPS as a fallback."""
    try:
        resp = requests.get(
            'https://dns.google/resolve',
            params={'name': host, 'type': 'A'},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        for answer in data.get('Answer', []):
            if answer.get('type') == 1 and answer.get('data'):
                return answer['data']

        # If no IPv4, attempt IPv6
        resp_v6 = requests.get(
            'https://dns.google/resolve',
            params={'name': host, 'type': 'AAAA'},
            timeout=5,
        )
        resp_v6.raise_for_status()
        data_v6 = resp_v6.json()
        for answer in data_v6.get('Answer', []):
            if answer.get('type') == 28 and answer.get('data'):
                return answer['data']

    except requests.RequestException:
        return None

    return None


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
        conn_params, host_meta = build_connection_params(db_url)

        # Read SQL file
        print("[1/3] Reading supabase_schema.sql...")
        with open('supabase_schema.sql', 'r') as f:
            sql_content = f.read()
        print("      [OK] SQL file loaded (75 lines)")

        # Connect to database
        print("[2/3] Connecting to Supabase...")
        if host_meta['original_host'] != host_meta['resolved_host']:
            print(f"      [i] DNS resolved {host_meta['original_host']} -> {host_meta['resolved_host']}")
        conn = connect(**conn_params)
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

    except (DatabaseError, InterfaceError) as e:
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

    except ValueError as e:
        print(f"\n[!!] Invalid database URL: {e}")
        return False

    except RuntimeError as e:
        print(f"\n[!!] Network error: {e}")
        print("Make sure your network allows outbound access to Supabase and retry.")
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
