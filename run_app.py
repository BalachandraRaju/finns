#!/usr/bin/env python3
"""
Run the trading application with proper configuration.
"""

import os
import sys
import subprocess

# Set up environment
os.chdir('/Users/balachandra.raju/projects/finns')
sys.path.insert(0, '/Users/balachandra.raju/projects/finns')

print("🚀 Starting Trading Application...")
print("📊 Point & Figure Charts with Fibonacci Levels")
print("🔧 Loading configuration...")

# Check if .env file exists and has Upstox token
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    upstox_token = os.getenv("UPSTOX_ACCESS_TOKEN")
    if upstox_token:
        print(f"✅ Upstox token configured: {upstox_token[:10]}...")
    else:
        print("⚠️ Upstox token not found in .env file")
        
except Exception as e:
    print(f"❌ Error loading environment: {e}")

print("🌐 Starting server on http://localhost:8000")
print("🧪 Test charts: http://localhost:8000/test-charts")
print("=" * 60)

# Start the server
try:
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ]
    
    env = os.environ.copy()
    env['PYTHONPATH'] = '/Users/balachandra.raju/projects/finns'
    
    subprocess.run(cmd, env=env, cwd='/Users/balachandra.raju/projects/finns')
    
except KeyboardInterrupt:
    print("\n👋 Server stopped by user")
except Exception as e:
    print(f"❌ Error starting server: {e}")
