import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config import settings


def init_database():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(settings.database_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            original_pdf_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)
    
    # Create recipients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipients (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            token TEXT NOT NULL,
            signed_at INTEGER,
            created_at INTEGER NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        )
    """)
    
    # Create index on recipient_id for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recipients_recipient_id 
        ON recipients (recipient_id)
    """)
    
    # Create fields table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fields (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            type TEXT NOT NULL,
            page INTEGER NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            width REAL NOT NULL,
            height REAL NOT NULL,
            label TEXT NOT NULL,
            value TEXT,
            signature_data TEXT,
            created_at INTEGER NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        )
    """)
    
    # Create index on document_id for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fields_document_id 
        ON fields (document_id)
    """)
    
    conn.commit()
    conn.close()


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def dict_from_row(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a dictionary."""
    return dict(zip(row.keys(), row))
