import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from config import DATABASE_PATH

class DealDatabase:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create deals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deals (
                    id INTEGER PRIMARY KEY,
                    deal_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    store TEXT NOT NULL,
                    price REAL NOT NULL,
                    max_quantity INTEGER NOT NULL,
                    current_quantity INTEGER DEFAULT 0,
                    your_commitment INTEGER DEFAULT 0,
                    link TEXT,
                    delivery_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create notifications table to track sent notifications
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY,
                    deal_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (deal_id) REFERENCES deals (deal_id)
                )
            ''')
            
            # Check if your_commitment column exists, if not add it
            cursor.execute("PRAGMA table_info(deals)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'your_commitment' not in columns:
                cursor.execute('ALTER TABLE deals ADD COLUMN your_commitment INTEGER DEFAULT 0')
                print("Added your_commitment column to existing database")
            
            conn.commit()
    
    def add_deal(self, deal_data: Dict) -> bool:
        """Add a new deal to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO deals 
                    (deal_id, title, store, price, max_quantity, current_quantity, your_commitment, link, delivery_date, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    deal_data['deal_id'],
                    deal_data['title'],
                    deal_data['store'],
                    deal_data['price'],
                    deal_data['max_quantity'],
                    deal_data.get('current_quantity', 0),
                    deal_data.get('your_commitment', 0),
                    deal_data.get('link', ''),
                    deal_data.get('delivery_date', ''),
                    datetime.now()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding deal: {e}")
            return False
    
    def get_all_deals(self) -> List[Dict]:
        """Get all deals from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT deal_id, title, store, price, max_quantity, current_quantity, your_commitment, link, delivery_date, created_at, updated_at
                FROM deals 
                ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_deal_by_id(self, deal_id: str) -> Optional[Dict]:
        """Get a specific deal by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT deal_id, title, store, price, max_quantity, current_quantity, your_commitment, link, delivery_date, created_at, updated_at
                FROM deals 
                WHERE deal_id = ?
            ''', (deal_id,))
            row = cursor.fetchone()
            
            return dict(row) if row else None
    
    def deal_exists(self, deal_id: str) -> bool:
        """Check if a deal exists in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM deals WHERE deal_id = ?', (deal_id,))
            return cursor.fetchone() is not None
    
    def update_deal_quantity(self, deal_id: str, current_quantity: int):
        """Update the current quantity for a deal."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE deals 
                SET current_quantity = ?, updated_at = ? 
                WHERE deal_id = ?
            ''', (current_quantity, datetime.now(), deal_id))
            conn.commit()
    
    def mark_notification_sent(self, deal_id: str, notification_type: str):
        """Mark that a notification has been sent for a deal."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notifications (deal_id, notification_type)
                VALUES (?, ?)
            ''', (deal_id, notification_type))
            conn.commit()
    
    def has_notification_been_sent(self, deal_id: str, notification_type: str) -> bool:
        """Check if a notification has already been sent for a deal."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM notifications 
                WHERE deal_id = ? AND notification_type = ?
            ''', (deal_id, notification_type))
            return cursor.fetchone() is not None
    
    def get_new_deals(self, since_timestamp: datetime) -> List[Dict]:
        """Get deals created after a specific timestamp."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM deals 
                WHERE created_at > ? 
                ORDER BY created_at DESC
            ''', (since_timestamp,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_your_commitment(self, deal_id: str, your_commitment: int):
        """Update the user's commitment quantity for a deal."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE deals 
                SET your_commitment = ?, updated_at = ? 
                WHERE deal_id = ?
            ''', (your_commitment, datetime.now(), deal_id))
            conn.commit()
    
    def get_active_deals(self) -> List[Dict]:
        """Get active deals from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT deal_id, title, store, price, max_quantity, current_quantity, your_commitment, link, delivery_date, created_at, updated_at
                FROM deals 
                WHERE current_quantity > 0
                ORDER BY created_at DESC
            ''')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows] 