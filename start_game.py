#!/usr/bin/env python3
"""
Wheel of Fortune Toss-up Game Launcher
Starts both frontend and backend servers
"""

import os
import sys
import time
import subprocess
import signal
import threading
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

class GameLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.shutdown = False
    
    def signal_handler(self, signum, frame):
        print("\n🛑 Shutting down servers...")
        self.shutdown = True
        self.stop_servers()
        sys.exit(0)
    
    def stop_servers(self):
        """Stop both frontend and backend servers"""
        if self.backend_process:
            print("📡 Stopping backend server...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        
        if self.frontend_process:
            print("🌐 Stopping frontend server...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
    
    def start_backend(self):
        """Start the backend server"""
        print("🚀 Starting backend server...")
        try:
            os.chdir(BACKEND_DIR)
            self.backend_process = subprocess.Popen([
                sys.executable, "start_server.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Wait a moment and check if it started successfully
            time.sleep(2)
            if self.backend_process.poll() is None:
                print("✅ Backend server started successfully on port 8001")
                return True
            else:
                print("❌ Backend server failed to start")
                return False
        except Exception as e:
            print(f"❌ Error starting backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the frontend server"""
        print("🌐 Starting frontend server...")
        try:
            os.chdir(FRONTEND_DIR)
            self.frontend_process = subprocess.Popen([
                sys.executable, "-m", "http.server", "3000"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Wait a moment and check if it started successfully
            time.sleep(1)
            if self.frontend_process.poll() is None:
                print("✅ Frontend server started successfully on port 3000")
                return True
            else:
                print("❌ Frontend server failed to start")
                return False
        except Exception as e:
            print(f"❌ Error starting frontend: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor both processes and restart if needed"""
        while not self.shutdown:
            if self.backend_process and self.backend_process.poll() is not None:
                print("⚠️  Backend server stopped unexpectedly")
                break
            
            if self.frontend_process and self.frontend_process.poll() is not None:
                print("⚠️  Frontend server stopped unexpectedly")
                break
            
            time.sleep(5)
    
    def run(self):
        """Start both servers and monitor them"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🎡 Wheel of Fortune Toss-up Game Launcher")
        print("=" * 50)
        
        # Start backend server
        if not self.start_backend():
            print("❌ Failed to start backend server")
            return False
        
        # Start frontend server
        if not self.start_frontend():
            print("❌ Failed to start frontend server")
            self.stop_servers()
            return False
        
        print("\n🎮 Game servers are running!")
        print("🌐 Frontend: http://localhost:3000")
        print("📡 Backend:  http://localhost:8001")
        print("🎡 Open http://localhost:3000 in your browser to play!")
        print("\nPress Ctrl+C to stop all servers")
        print("=" * 50)
        
        # Monitor processes
        try:
            self.monitor_processes()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_servers()
        
        return True

if __name__ == "__main__":
    # Check if we're in a virtual environment
    if not os.getenv('VIRTUAL_ENV'):
        print("⚠️  Warning: No virtual environment detected")
        print("   Consider running: source .venv/bin/activate")
        print()
    
    launcher = GameLauncher()
    success = launcher.run()
    
    if success:
        print("👋 Game servers stopped successfully")
    else:
        print("❌ Failed to start game servers")
        sys.exit(1)
