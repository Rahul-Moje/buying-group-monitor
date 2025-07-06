#!/usr/bin/env python3
"""
Buying Group Monitor - Main Entry Point

This script monitors the buying group website for new deals and sends notifications.
"""

import argparse
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from monitor import BuyingGroupMonitor
import logging
from config import LOG_LEVEL
import json
import time
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'healthy',
                'timestamp': time.time(),
                'service': 'Buying Group Monitor'
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Get monitor status if available
            try:
                monitor = BuyingGroupMonitor()
                status = monitor.get_status()
                response = status
            except Exception as e:
                response = {
                    'error': str(e),
                    'status': 'error'
                }
            
            self.wfile.write(json.dumps(response).encode())
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
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Buying Group Monitor')
    parser.add_argument('command', choices=['start', 'status'], 
                       help='Command to run')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port for health check server (default: 8000)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()))
    logger = logging.getLogger('main')
    
    if args.command == 'status':
        logger.info("Getting monitor status...")
        try:
            monitor = BuyingGroupMonitor()
            status = monitor.get_status()
            print("Monitor Status:")
            print(f"  Running: {status['running']}")
            print(f"  Health: {status['health']}")
            print(f"  Config: {status['config']}")
        except Exception as e:
            logger.error(f"Error getting status: {e}", exc_info=True)
            sys.exit(1)
    
    elif args.command == 'start':
        logger.info("Starting Buying Group Monitor...")
        
        try:
            # Create monitor instance
            monitor = BuyingGroupMonitor()
            
            # Start health check server
            start_health_server(args.port)
            
            # Start the monitor
            monitor.start()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down...")
            if 'monitor' in locals():
                monitor.stop()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error starting monitor: {e}", exc_info=True)
            sys.exit(1)

if __name__ == '__main__':
    main() 