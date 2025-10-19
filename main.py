#!/usr/bin/env python
"""
Main entry point for Diagram Generator v3.
Starts the REST API server.
"""

import logging
from rest_server import run_server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("Starting Diagram Generator v3 REST API...")
    run_server()
