import sqlite3
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional
from config import DATABASE_PATH
import os

class DealDatabase:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        try:
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
                
                # Create notifications table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY,
                        batch_id TEXT UNIQUE NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Check if your_commitment column exists, add if not
                cursor.execute("PRAGMA table_info(deals)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'your_commitment' not in columns:
                    self.logger.info("Adding your_commitment column to deals table")
                    cursor.execute('''
                        ALTER TABLE deals 
                        ADD COLUMN your_commitment INTEGER DEFAULT 0
                    ''')
                    self.logger.info("Successfully added your_commitment column")
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}", exc_info=True)
            raise
    
    def _validate_deal_data(self, deal: Dict) -> bool:
        """Validate deal data before database operations."""
        required_fields = ['deal_id', 'title', 'store', 'price', 'max_quantity']
        for field in required_fields:
            if field not in deal or deal[field] is None:
                self.logger.warning(f"Deal missing required field: {field}")
                return False
        
        # Validate data types
        if not isinstance(deal['deal_id'], str) or not deal['deal_id'].strip():
            self.logger.warning("Deal ID must be a non-empty string")
            return False
        
        if not isinstance(deal['title'], str) or not deal['title'].strip():
            self.logger.warning("Deal title must be a non-empty string")
            return False
        
        if not isinstance(deal['store'], str) or not deal['store'].strip():
            self.logger.warning("Deal store must be a non-empty string")
            return False
        
        if not isinstance(deal['price'], (int, float)) or deal['price'] < 0:
            self.logger.warning("Deal price must be a non-negative number")
            return False
        
        if not isinstance(deal['max_quantity'], int) or deal['max_quantity'] < 0:
            self.logger.warning("Deal max_quantity must be a non-negative integer")
            return False
        
        return True
    
    def add_deal(self, deal: Dict) -> bool:
        """Add a new deal to the database."""
        if not self._validate_deal_data(deal):
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO deals 
                    (deal_id, title, store, price, max_quantity, current_quantity, 
                     your_commitment, link, delivery_date, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    deal['deal_id'],
                    deal['title'],
                    deal['store'],
                    deal['price'],
                    deal['max_quantity'],
                    deal.get('current_quantity', 0),
                    deal.get('your_commitment', 0),
                    deal.get('link', ''),
                    deal.get('delivery_date', ''),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                self.logger.debug(f"Successfully added/updated deal: {deal['title']}")
                return True
                
        except sqlite3.IntegrityError as e:
            self.logger.warning(f"Integrity error adding deal {deal['deal_id']}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error adding deal: {e}", exc_info=True)
            return False
    
    def get_all_deals(self) -> List[Dict]:
        """Get all deals from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT deal_id, title, store, price, max_quantity, 
                           current_quantity, your_commitment, link, delivery_date,
                           created_at, updated_at
                    FROM deals 
                    ORDER BY created_at DESC
                ''')
                
                deals = []
                for row in cursor.fetchall():
                    deals.append({
                        'deal_id': row[0],
                        'title': row[1],
                        'store': row[2],
                        'price': row[3],
                        'max_quantity': row[4],
                        'current_quantity': row[5],
                        'your_commitment': row[6],
                        'link': row[7],
                        'delivery_date': row[8],
                        'created_at': row[9],
                        'updated_at': row[10]
                    })
                
                self.logger.debug(f"Retrieved {len(deals)} deals from database")
                return deals
                
        except Exception as e:
            self.logger.error(f"Error getting all deals: {e}", exc_info=True)
            return []
    
    def get_deal_by_id(self, deal_id: str) -> Optional[Dict]:
        """Get a deal by its ID."""
        if not deal_id or not isinstance(deal_id, str):
            self.logger.warning("Invalid deal_id provided")
            return None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT deal_id, title, store, price, max_quantity, 
                           current_quantity, your_commitment, link, delivery_date,
                           created_at, updated_at
                    FROM deals 
                    WHERE deal_id = ?
                ''', (deal_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'deal_id': row[0],
                        'title': row[1],
                        'store': row[2],
                        'price': row[3],
                        'max_quantity': row[4],
                        'current_quantity': row[5],
                        'your_commitment': row[6],
                        'link': row[7],
                        'delivery_date': row[8],
                        'created_at': row[9],
                        'updated_at': row[10]
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting deal by ID: {e}", exc_info=True)
            return None
    
    def deal_exists(self, deal_id: str) -> bool:
        """Check if a deal exists in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM deals WHERE deal_id = ?', (deal_id,))
            return cursor.fetchone() is not None
    
    def update_deal_quantity(self, deal_id: str, new_quantity: int) -> bool:
        """Update the current quantity for a deal."""
        if not deal_id or not isinstance(deal_id, str):
            self.logger.warning("Invalid deal_id provided for quantity update")
            return False
        
        if not isinstance(new_quantity, int) or new_quantity < 0:
            self.logger.warning("Invalid quantity value provided")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE deals 
                    SET current_quantity = ?, updated_at = ?
                    WHERE deal_id = ?
                ''', (new_quantity, datetime.now().isoformat(), deal_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.debug(f"Updated quantity for deal {deal_id} to {new_quantity}")
                    return True
                else:
                    self.logger.warning(f"No deal found with ID {deal_id} for quantity update")
                    return False
                
        except Exception as e:
            self.logger.error(f"Error updating deal quantity: {e}", exc_info=True)
            return False
    
    def update_your_commitment(self, deal_id: str, commitment: int) -> bool:
        """Update your commitment quantity for a deal."""
        if not deal_id or not isinstance(deal_id, str):
            self.logger.warning("Invalid deal_id provided for commitment update")
            return False
        
        if not isinstance(commitment, int) or commitment < 0:
            self.logger.warning("Invalid commitment value provided")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE deals 
                    SET your_commitment = ?, updated_at = ?
                    WHERE deal_id = ?
                ''', (commitment, datetime.now().isoformat(), deal_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.debug(f"Updated commitment for deal {deal_id} to {commitment}")
                    return True
                else:
                    self.logger.warning(f"No deal found with ID {deal_id} for commitment update")
                    return False
                
        except Exception as e:
            self.logger.error(f"Error updating deal commitment: {e}", exc_info=True)
            return False
    
    def has_notification_been_sent(self, batch_id: str) -> bool:
        """Check if a notification has been sent for a batch."""
        if not batch_id or not isinstance(batch_id, str):
            self.logger.warning("Invalid batch_id provided")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM notifications 
                    WHERE batch_id = ?
                ''', (batch_id,))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"Error checking notification status: {e}", exc_info=True)
            return False
    
    def mark_notification_sent(self, batch_id: str) -> bool:
        """Mark a notification as sent for a batch."""
        if not batch_id or not isinstance(batch_id, str):
            self.logger.warning("Invalid batch_id provided")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO notifications (batch_id)
                    VALUES (?)
                ''', (batch_id,))
                
                conn.commit()
                self.logger.debug(f"Marked notification sent for batch {batch_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error marking notification sent: {e}", exc_info=True)
            return False
    
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
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total deals
                cursor.execute('SELECT COUNT(*) FROM deals')
                total_deals = cursor.fetchone()[0]
                
                # Active deals (with commitments)
                cursor.execute('SELECT COUNT(*) FROM deals WHERE your_commitment > 0')
                active_deals = cursor.fetchone()[0]
                
                # Total commitment value
                cursor.execute('''
                    SELECT SUM(price * your_commitment) 
                    FROM deals 
                    WHERE your_commitment > 0
                ''')
                total_value = cursor.fetchone()[0] or 0
                
                # Recent deals (last 7 days)
                cursor.execute('''
                    SELECT COUNT(*) FROM deals 
                    WHERE created_at >= datetime('now', '-7 days')
                ''')
                recent_deals = cursor.fetchone()[0]
                
                return {
                    'total_deals': total_deals,
                    'active_deals': active_deals,
                    'total_value': round(total_value, 2),
                    'recent_deals': recent_deals
                }
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}", exc_info=True)
            return {
                'total_deals': 0,
                'active_deals': 0,
                'total_value': 0,
                'recent_deals': 0
            } 