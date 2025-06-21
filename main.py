#!/usr/bin/env python3
"""
Buying Group Monitor - Main Entry Point

This script monitors the buying group website for new deals and sends notifications.
"""

import argparse
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from monitor import BuyingGroupMonitor

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server(port=8000):
    """Start a simple HTTP server for health checks."""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"Health check server started on port {port}")

def main():
    parser = argparse.ArgumentParser(
        description="Monitor buying group for new deals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py start          # Start continuous monitoring
  python main.py check          # Run a single check
  python main.py stats          # Show statistics
  python main.py test-login     # Test login credentials
  python main.py update-commitment <deal_id> <new_quantity>  # Update commitment for a specific deal
  python main.py summary        # Show summary of all deals
  python main.py list-commitments  # List all deals with their current commitments
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'check', 'stats', 'test-login', 'send-summary', 'update-commitment', 'summary', 'list-commitments'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'deal_id',
        nargs='?',
        help='Deal ID for update-commitment command'
    )
    
    parser.add_argument(
        'new_quantity',
        nargs='?',
        help='New quantity for update-commitment command'
    )
    
    args = parser.parse_args()
    
    # Create monitor instance
    monitor = BuyingGroupMonitor()
    
    try:
        if args.command == 'start':
            print("🚀 Starting Buying Group Monitor...")
            # Start health check server for cloud deployment
            start_health_server()
            monitor.start_monitoring()
            
        elif args.command == 'check':
            print("🔍 Running single check...")
            monitor.run_single_check()
            
        elif args.command == 'stats':
            print("📊 Getting statistics...")
            monitor.get_statistics()
            
        elif args.command == 'test-login':
            print("🔐 Testing login credentials...")
            if monitor.scraper.login():
                print("✅ Login successful!")
                deals = monitor.scraper.get_deals()
                print(f"Found {len(deals)} deals")
                if deals:
                    print("Sample deal:")
                    print(f"  Title: {deals[0]['title']}")
                    print(f"  Store: {deals[0]['store']}")
                    print(f"  Price: ${deals[0]['price']:.2f}")
            else:
                print("❌ Login failed!")
                sys.exit(1)
        elif args.command == 'send-summary':
            print("📋 Sending all active deals summary to Discord...")
            deals = monitor.database.get_all_deals()
            monitor.notifier.send_all_deals_summary(deals)
        elif args.command == 'update-commitment':
            if args.deal_id is None or args.new_quantity is None:
                print("Usage: python main.py update-commitment <deal_id> <new_quantity>")
                sys.exit(1)
            
            deal_id = args.deal_id
            try:
                new_quantity = int(args.new_quantity)
            except ValueError:
                print("Error: Quantity must be a number")
                sys.exit(1)
            
            # Get the deal from database
            deal = monitor.database.get_deal_by_id(deal_id)
            if not deal:
                print(f"Error: Deal with ID {deal_id} not found")
                sys.exit(1)
            
            old_commitment = deal.get('your_commitment', 0)
            
            # Update commitment in database
            monitor.database.update_your_commitment(deal_id, new_quantity)
            
            # Send notification about the change
            monitor.notifier.send_commitment_update_notification(deal, old_commitment, new_quantity)
            
            print(f"Updated commitment for {deal['title']}: {old_commitment} → {new_quantity}")
            print("Notification sent to Discord")
        elif args.command == 'summary':
            print("📋 Showing summary of all deals...")
            deals = monitor.database.get_all_deals()
            monitor.notifier.send_all_deals_summary(deals)
        elif args.command == 'list-commitments':
            print("📋 Your current commitments:")
            deals = monitor.database.get_all_deals()
            
            if not deals:
                print("No deals found in database")
                return
            
            for deal in deals:
                commitment = deal.get('your_commitment', 0)
                if commitment > 0:
                    print(f"• {deal['title']} ({deal['store']}) - ${deal['price']:.2f} - Qty: {commitment}")
                else:
                    print(f"• {deal['title']} ({deal['store']}) - ${deal['price']:.2f} - No commitment")
                
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 