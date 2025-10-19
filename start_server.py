#!/usr/bin/env python3
"""
Simple script to start the FastAPI server.
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    import uvicorn
    from app.main import app
    
    print("🚀 Starting FastAPI server...")
    print("📊 Trading application with P&F charts and Fibonacci levels")
    print("🌐 Server will be available at: http://localhost:8000")
    print("🧪 Test charts at: http://localhost:8000/test-charts")
    print("=" * 60)
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting server: {e}")
    sys.exit(1)
