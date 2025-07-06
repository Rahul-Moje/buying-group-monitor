import boto3
import json
import logging
from typing import List, Dict, Optional
from config import S3_BUCKET, S3_KEY
from botocore.exceptions import ClientError
import os
from datetime import datetime

class DealDatabase:
    def __init__(self, bucket: str = S3_BUCKET, key: str = S3_KEY):
        self.bucket = bucket
        self.key = key
        self.logger = logging.getLogger('deal_database')
        self.s3 = boto3.client('s3')

    def _load_deals(self) -> List[Dict]:
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=self.key)
            deals = json.loads(response['Body'].read().decode('utf-8'))
            return deals
        except self.s3.exceptions.NoSuchKey:
            return []
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return []
            self.logger.error(f"Error loading deals from S3: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error loading deals from S3: {e}")
            return []

    def _save_deals(self, deals: List[Dict]):
        try:
            self.s3.put_object(Bucket=self.bucket, Key=self.key, Body=json.dumps(deals))
        except Exception as e:
            self.logger.error(f"Error saving deals to S3: {e}")

    def get_all_deals(self) -> List[Dict]:
        return self._load_deals()

    def add_deal(self, deal: Dict) -> bool:
        deals = self._load_deals()
        for i, d in enumerate(deals):
            if d['deal_id'] == deal['deal_id']:
                deals[i] = deal
                self._save_deals(deals)
                return True
        deals.append(deal)
        self._save_deals(deals)
        return True

    def deal_exists(self, deal_id: str) -> bool:
        deals = self._load_deals()
        return any(d['deal_id'] == deal_id for d in deals)

    def get_deal_by_id(self, deal_id: str) -> Optional[Dict]:
        deals = self._load_deals()
        for d in deals:
            if d['deal_id'] == deal_id:
                return d
        return None

    def get_new_deals(self, since_timestamp):
        deals = self._load_deals()
        return [d for d in deals if d.get('created_at', '') > since_timestamp]

    def get_active_deals(self) -> List[Dict]:
        deals = self._load_deals()
        return [d for d in deals if d.get('current_quantity', 0) > 0]

    # Notification tracking can be handled similarly in S3 or skipped for simplicity
    def has_notification_been_sent(self, batch_id: str) -> bool:
        # For simplicity, skip notification deduplication or store a notification log in S3 if needed
        return False

    def mark_notification_sent(self, batch_id: str) -> bool:
        # For simplicity, skip notification deduplication or store a notification log in S3 if needed
        return True

    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            deals = self._load_deals()
            
            # Total deals
            total_deals = len(deals)
            
            # Active deals (with commitments)
            active_deals = sum(1 for d in deals if d.get('current_quantity', 0) > 0)
            
            # Total commitment value
            total_value = sum(d.get('price', 0) * d.get('current_quantity', 0) for d in deals)
            
            # Recent deals (last 7 days)
            recent_deals = sum(1 for d in deals if (datetime.now() - datetime.fromisoformat(d.get('created_at', ''))).days <= 7)
            
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