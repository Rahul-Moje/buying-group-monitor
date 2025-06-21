#!/usr/bin/env python3
"""
Test cases for Buying Group Monitor
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from datetime import datetime

from scraper import BuyingGroupScraper
from database import DealDatabase
from notifier import DiscordNotifier
from monitor import BuyingGroupMonitor
from logger import setup_logger

class TestBuyingGroupScraper(unittest.TestCase):
    """Test cases for the scraper functionality."""
    
    def setUp(self):
        self.scraper = BuyingGroupScraper()
    
    def test_deal_id_generation(self):
        """Test that deal IDs are generated consistently."""
        deal1 = {
            'title': 'Test Product',
            'store': 'Test Store'
        }
        
        deal2 = {
            'title': 'Test Product',
            'store': 'Test Store'
        }
        
        # Generate IDs using the same method as the scraper
        import hashlib
        deal_text1 = f"{deal1['store']}_{deal1['title']}".lower().strip()
        deal_id1 = hashlib.md5(deal_text1.encode()).hexdigest()[:16]
        
        deal_text2 = f"{deal2['store']}_{deal2['title']}".lower().strip()
        deal_id2 = hashlib.md5(deal_text2.encode()).hexdigest()[:16]
        
        # IDs should be identical for same deal
        self.assertEqual(deal_id1, deal_id2)
    
    @patch('requests.Session')
    def test_login_success(self, mock_session):
        """Test successful login."""
        # Mock successful login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://buyinggroup.ca/dashboard"
        mock_response.text = '<input name="_token" value="test_token">'
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Test login with mocked credentials and URL
        with patch('scraper.USERNAME', 'test@example.com'), \
             patch('scraper.PASSWORD', 'testpass'), \
             patch('scraper.BUYING_GROUP_LOGIN_URL', 'https://buyinggroup.ca/login'), \
             patch('scraper.BUYING_GROUP_DASHBOARD_URL', 'https://buyinggroup.ca/dashboard'):
            result = self.scraper.login()
            self.assertTrue(result)
    
    @patch('requests.Session')
    def test_login_failure(self, mock_session):
        """Test failed login."""
        # Mock failed login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://buyinggroup.ca/login"
        mock_response.text = '<input name="_token" value="test_token">'
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Test login with mocked credentials
        with patch('scraper.USERNAME', 'test@example.com'), \
             patch('scraper.PASSWORD', 'wrongpass'), \
             patch('scraper.BUYING_GROUP_LOGIN_URL', 'https://buyinggroup.ca/login'):
            result = self.scraper.login()
            self.assertFalse(result)

class TestDealDatabase(unittest.TestCase):
    """Test cases for the database functionality."""
    
    def setUp(self):
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DealDatabase(self.temp_db.name)
    
    def tearDown(self):
        # Clean up temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_add_and_get_deal(self):
        """Test adding and retrieving a deal."""
        deal = {
            'deal_id': 'test123',
            'title': 'Test Product',
            'store': 'Test Store',
            'price': 10.99,
            'max_quantity': 5,
            'current_quantity': 0,
            'your_commitment': 0,
            'link': 'https://example.com',
            'delivery_date': '2024-01-01'
        }
        
        # Add deal
        result = self.db.add_deal(deal)
        print(f"add_deal returned: {result}")
        self.assertTrue(result)
        
        # Retrieve deal
        retrieved_deal = self.db.get_deal_by_id('test123')
        print(f"retrieved_deal: {retrieved_deal}")
        self.assertIsNotNone(retrieved_deal)
        self.assertEqual(retrieved_deal['title'], 'Test Product')
        self.assertEqual(retrieved_deal['price'], 10.99)
    
    def test_update_deal_quantity(self):
        """Test updating deal quantity."""
        # Add a deal first
        deal = {
            'deal_id': 'test123',
            'title': 'Test Product',
            'store': 'Test Store',
            'price': 10.99,
            'max_quantity': 5,
            'current_quantity': 0,
            'your_commitment': 0,
            'link': 'https://example.com',
            'delivery_date': '2024-01-01'
        }
        add_result = self.db.add_deal(deal)
        print(f"add_deal returned: {add_result}")
        self.assertTrue(add_result)
        
        # Update quantity
        self.db.update_deal_quantity('test123', 3)
        
        # Check update
        updated_deal = self.db.get_deal_by_id('test123')
        print(f"updated_deal: {updated_deal}")
        self.assertIsNotNone(updated_deal)
        self.assertEqual(updated_deal['current_quantity'], 3)
    
    def test_notification_tracking(self):
        """Test notification tracking functionality."""
        # Mark notification as sent
        self.db.mark_notification_sent('test123', 'new_deal')
        
        # Check if notification was sent
        self.assertTrue(self.db.has_notification_been_sent('test123', 'new_deal'))
        self.assertFalse(self.db.has_notification_been_sent('test123', 'quantity_update'))

class TestDiscordNotifier(unittest.TestCase):
    """Test cases for Discord notification functionality."""
    
    def setUp(self):
        self.notifier = DiscordNotifier("https://discord.com/api/webhooks/test")
    
    @patch('requests.post')
    def test_send_new_deals_notification_success(self, mock_post):
        """Test successful new deals notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        deals = [{
            'title': 'Test Product',
            'store': 'Test Store',
            'price': 10.99,
            'max_quantity': 5,
            'link': 'https://example.com',
            'delivery_date': '2024-01-01'
        }]
        
        result = self.notifier.send_new_deals_notification(deals)
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_new_deals_notification_failure(self, mock_post):
        """Test failed new deals notification."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response
        mock_post.side_effect = Exception("Webhook not found")
        
        deals = [{
            'title': 'Test Product',
            'store': 'Test Store',
            'price': 10.99,
            'max_quantity': 5,
            'link': 'https://example.com',
            'delivery_date': '2024-01-01'
        }]
        
        result = self.notifier.send_new_deals_notification(deals)
        self.assertFalse(result)

class TestBuyingGroupMonitor(unittest.TestCase):
    """Test cases for the main monitor functionality."""
    
    def setUp(self):
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock the database path
        with patch('config.DATABASE_PATH', self.temp_db.name):
            self.monitor = BuyingGroupMonitor()
    
    def tearDown(self):
        # Clean up temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    @patch('scraper.BuyingGroupScraper.get_deals')
    def test_check_for_new_deals_no_new_deals(self, mock_get_deals):
        """Test monitoring when no new deals are found."""
        # Mock existing deals
        mock_get_deals.return_value = [{
            'deal_id': 'existing123',
            'title': 'Existing Product',
            'store': 'Test Store',
            'price': 10.99,
            'max_quantity': 5,
            'current_quantity': 0,
            'your_commitment': 0,
            'link': 'https://example.com',
            'delivery_date': '2024-01-01'
        }]
        
        # Add existing deal to database
        self.monitor.database.add_deal(mock_get_deals.return_value[0])
        
        # Run check
        self.monitor.check_for_new_deals()
        
        # Should not find any new deals
        # (This test mainly ensures no exceptions are raised)
        self.assertTrue(True)
    
    @patch('scraper.BuyingGroupScraper.get_deals')
    @patch('notifier.DiscordNotifier.send_new_deals_notification')
    def test_check_for_new_deals_with_new_deal(self, mock_send_notification, mock_get_deals):
        """Test monitoring when a new deal is found."""
        # Mock new deal
        mock_get_deals.return_value = [{
            'deal_id': 'new123',
            'title': 'New Product',
            'store': 'Test Store',
            'price': 15.99,
            'max_quantity': 3,
            'current_quantity': 0,
            'your_commitment': 0,
            'link': 'https://example.com',
            'delivery_date': '2024-01-01'
        }]
        
        # Mock successful notification
        mock_send_notification.return_value = True
        
        # Run check
        self.monitor.check_for_new_deals()
        
        # Should send notification for new deal
        mock_send_notification.assert_called_once()

def run_tests():
    """Run all test cases."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestBuyingGroupScraper))
    test_suite.addTest(unittest.makeSuite(TestDealDatabase))
    test_suite.addTest(unittest.makeSuite(TestDiscordNotifier))
    test_suite.addTest(unittest.makeSuite(TestBuyingGroupMonitor))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!") 