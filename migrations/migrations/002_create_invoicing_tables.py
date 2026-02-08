"""
Migration: Create invoicing tables
Version: 002
Description: Creates clients, products, invoices, and invoice_items tables with seed data.
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DATABASE_PATH


def upgrade():
    """Apply the migration."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        "SELECT 1 FROM _migrations WHERE name = ?",
        ("002_create_invoicing_tables",),
    )
    if cursor.fetchone():
        print("Migration 002_create_invoicing_tables already applied. Skipping.")
        conn.close()
        return

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            company_registration_no TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL UNIQUE,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            client_id INTEGER NOT NULL,
            address TEXT NOT NULL,
            tax REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """
    )

    sample_clients = [
        ("Stellar Industries", "100 Market Street, Springfield", "REG-10001"),
        ("Nova Retail Co.", "42 Galaxy Way, Horizon City", "REG-10002"),
        ("Aurora Health", "88 Northern Lights Ave, Summit", "REG-10003"),
    ]
    cursor.executemany(
        "INSERT INTO clients (name, address, company_registration_no) VALUES (?, ?, ?)",
        sample_clients,
    )

    sample_products = [
        ("Website Design", 1500.00),
        ("Monthly Hosting", 120.00),
        ("Consulting Session", 300.00),
        ("Analytics Setup", 500.00),
    ]
    cursor.executemany(
        "INSERT INTO products (name, price) VALUES (?, ?)",
        sample_products,
    )

    cursor.execute(
        "INSERT INTO _migrations (name) VALUES (?)",
        ("002_create_invoicing_tables",),
    )

    conn.commit()
    conn.close()
    print("Migration 002_create_invoicing_tables applied successfully.")


def downgrade():
    """Revert the migration."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS invoice_items")
    cursor.execute("DROP TABLE IF EXISTS invoices")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS clients")

    cursor.execute(
        "DELETE FROM _migrations WHERE name = ?",
        ("002_create_invoicing_tables",),
    )

    conn.commit()
    conn.close()
    print("Migration 002_create_invoicing_tables reverted successfully.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run database migration")
    parser.add_argument(
        "action",
        choices=["upgrade", "downgrade"],
        help="Migration action to perform",
    )

    args = parser.parse_args()

    if args.action == "upgrade":
        upgrade()
    elif args.action == "downgrade":
        downgrade()
