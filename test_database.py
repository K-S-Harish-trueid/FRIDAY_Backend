"""
Simple DB connection tester for F.R.I.D.A.Y backend.
Run this directly to isolate whether the issue is DNS/network or app config.

Usage:
    python test_db_connection.py
"""

import asyncio
import os
import socket
import sys

# Load .env manually so this works standalone, same folder as your app
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, relying on already-set env vars")

DATABASE_URL = os.getenv("DATABASE_URL")


def mask(url: str) -> str:
    if not url:
        return "None"
    if "@" in url:
        creds, rest = url.split("@", 1)
        if ":" in creds:
            scheme_user, _pwd = creds.rsplit(":", 1)
            return f"{scheme_user}:****@{rest}"
    return url


def get_host_port(url: str):
    # crude parse: postgresql+asyncpg://user:pass@host:port/db
    try:
        after_at = url.split("@", 1)[1]
        host_port = after_at.split("/", 1)[0]
        if ":" in host_port:
            host, port = host_port.split(":", 1)
            return host, int(port)
        return host_port, 5432
    except Exception as e:
        print(f"Could not parse host/port from DATABASE_URL: {e}")
        return None, None


def check_dns(host: str):
    print(f"\n[1/3] Resolving DNS for host: {host}")
    try:
        infos = socket.getaddrinfo(host, None)
        ips = sorted({info[4][0] for info in infos})
        print(f"  ✓ DNS OK — resolved to: {ips}")
        return True
    except socket.gaierror as e:
        print(f"  ✗ DNS FAILED: {e}")
        print("  -> This means the hostname is wrong, or your network/DNS")
        print("     can't reach it. If this is a Supabase 'db.<ref>.supabase.co'")
        print("     host, try the pooler host instead (aws-0-<region>.pooler.supabase.com).")
        return False


def check_tcp(host: str, port: int):
    print(f"\n[2/3] Testing raw TCP connect to {host}:{port}")
    try:
        with socket.create_connection((host, port), timeout=5):
            print("  ✓ TCP connection OK")
            return True
    except Exception as e:
        print(f"  ✗ TCP connect FAILED: {e}")
        print("  -> DNS resolved but the port isn't reachable. Check firewall,")
        print("     VPN, or whether you need the pooler port (6543) instead of 5432.")
        return False


async def check_asyncpg(url: str):
    print("\n[3/3] Testing actual Postgres connection via asyncpg")
    try:
        import asyncpg
    except ImportError:
        print("  ⚠️  asyncpg not installed, skipping. Run: pip install asyncpg")
        return False

    # asyncpg wants plain postgresql:// not postgresql+asyncpg://
    plain_url = url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        conn = await asyncpg.connect(plain_url, timeout=10)
        version = await conn.fetchval("SELECT version();")
        await conn.close()
        print("  ✓ Postgres connection OK")
        print(f"  Server version: {version}")
        return True
    except Exception as e:
        print(f"  ✗ Postgres connection FAILED: {type(e).__name__}: {e}")
        return False


def main():
    print("=" * 60)
    print("F.R.I.D.A.Y — Database Connection Tester")
    print("=" * 60)

    if not DATABASE_URL:
        print("\n✗ DATABASE_URL is not set. Check your .env file and that")
        print("  it's in the same directory you're running this script from.")
        sys.exit(1)

    print(f"\nDATABASE_URL (masked): {mask(DATABASE_URL)}")

    host, port = get_host_port(DATABASE_URL)
    if not host:
        sys.exit(1)

    dns_ok = check_dns(host)
    if not dns_ok:
        print("\nStopping here — fix DNS/hostname before testing further.")
        sys.exit(1)

    tcp_ok = check_tcp(host, port)
    if not tcp_ok:
        print("\nStopping here — fix network/firewall/port before testing further.")
        sys.exit(1)

    asyncio.run(check_asyncpg(DATABASE_URL))

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()