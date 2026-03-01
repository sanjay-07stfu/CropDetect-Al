#!/usr/bin/env python
"""
Quick Start Script for AI Crop Disease Detection System
Run this to automatically set up and start the application
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a shell command with user feedback"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def main():
    print("=" * 60)
    print("AI Crop Disease Detection System - Quick Start")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print(f"\n📍 Project directory: {project_dir}")
    
    # Step 1: Install dependencies
    print("\n" + "=" * 60)
    print("STEP 1: Installing Dependencies")
    print("=" * 60)
    
    if run_command("pip install -r requirements.txt", "Installing packages"):
        print("✓ Dependencies installed successfully")
    else:
        print("⚠️  Some packages may already be installed")
    
    # Step 2: Run diagnostic
    print("\n" + "=" * 60)
    print("STEP 2: Running Diagnostic Check")
    print("=" * 60)
    
    if run_command("python diagnose.py", "Diagnostic check"):
        print("✓ All checks passed")
    else:
        print("⚠️  Some checks had warnings - see above")
    
    # Step 3: Start application
    print("\n" + "=" * 60)
    print("STEP 3: Starting Application")
    print("=" * 60)
    
    print("\n🚀 Launching Flask application...")
    print("   - Application will start at: http://localhost:5000")
    print("   - Press Ctrl+C to stop the server")
    print("\n   Opening browser in 3 seconds...")
    
    import time
    time.sleep(3)
    
    try:
        import webbrowser
        webbrowser.open('http://localhost:5000')
    except Exception as e:
        print(f"   (Could not auto-open browser: {e})")
    
    # Run Flask
    print("\n" + "=" * 60)
    try:
        os.system("python app.py")
    except KeyboardInterrupt:
        print("\n\n✓ Application stopped by user")
        print("=" * 60)

if __name__ == "__main__":
    main()
