"""
Chaos Engineering Test
Simulates system failures (killing the API, blocking ports) to verify resilience.
"""
import subprocess
import time
import os
import signal
import requests

def kill_api():
    """Simulate API crash"""
    print("🔥 Chaos: Killing API server...")
    # Find process on port 8000
    try:
        # Windows command to find PID on port 8000
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if ":8000" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                print(f"Killing PID: {pid}")
                subprocess.run(["taskkill", "/F", "/PID", pid])
                return True
    except Exception as e:
        print(f"Error killing API: {e}")
    return False

def check_resilience():
    """Verify if system is up"""
    try:
        resp = requests.get("http://localhost:8000/api/status", timeout=2)
        return resp.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🧪 Starting Chaos Test...")
    
    # 1. Check if healthy
    initial = check_resilience()
    print(f"Initial Health: {'UP' if initial else 'DOWN'}")
    
    if initial:
        # 2. Kill it
        kill_api()
        
        # 3. Wait for auto-restart (if implemented via systemd/docker)
        # Note: In our current local dev, it won't auto-restart unless we use a manager.
        # But this test documents the failure.
        time.sleep(2)
        after = check_resilience()
        print(f"Health after chaos: {'UP' if after else 'DOWN'}")
        
        if not after:
            print("⚠️ System did not auto-recover. Manual restart needed.")
        else:
            print("✅ System recovered automatically!")
    else:
        print("❌ System is already down. Cannot run chaos test.")
