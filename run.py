#!/usr/bin/env python3
"""
Simple script to run the StockWise Flask application
"""
from app import app

if __name__ == '__main__':
    print("\n" + "="*50)
    print("StockWise MVP - Starting Flask Application")
    print("="*50)
    print("Open your browser to: http://localhost:5001/upload")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
