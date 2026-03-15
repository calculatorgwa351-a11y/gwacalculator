#!/usr/bin/env python3
"""
Automated setup script for GWA Calculator with dummy data
Run this to completely set up the application with realistic test data
"""

import os
import sys
import time
import subprocess
import importlib.util

def check_and_install_requirements():
    """Check if required packages are installed, install if needed"""
    print("📦 Checking dependencies...")
    
    required_packages = ['flask', 'flask_sqlalchemy', 'faker', 'werkzeug']
    
    for package in required_packages:
        try:
            if package == 'flask_sqlalchemy':
                spec = importlib.util.find_spec('flask_sqlalchemy')
            elif package == 'werkzeug':
                spec = importlib.util.find_spec('werkzeug')
            else:
                spec = importlib.util.find_spec(package)
            
            if spec is None:
                print(f"📥 Installing {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
                print(f"✅ {package} installed")
            else:
                print(f"✅ {package} already installed")
        except ImportError:
            print(f"📥 Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def setup_direct():
    """Setup directly without Docker"""
    print("🔧 Setting up directly...")
    
    # Install dependencies first
    if not check_and_install_requirements():
        return False
    
    # Now import app modules
    try:
        from app import app, db
        from create_dummy_data import main
        
        with app.app_context():
            # Clear and recreate database
            db.drop_all()
            db.create_all()
            print("🗄️ Database initialized")
        
        # Generate dummy data
        main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Please run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False
    
    return True

def start_application():
    """Start the Flask application"""
    print("🚀 Starting application...")
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start application: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return True

def main_setup():
    """Main setup function"""
    print("� GWA Calculator Automated Setup")
    print("=" * 50)
    print("🔧 Using direct Python setup (no Docker)")
    
    # Setup directly
    success = setup_direct()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Access Information:")
        print("🌐 Application URL: http://localhost:5000")
        print("👤 Admin Login: admin / adminpass")
        print("🎓 Student Login: 2024xxxx / password123")
        print("\n📊 Data Analysis Endpoints:")
        print("   • GET /api/analytics/all_data - Complete dataset")
        print("   • GET /api/analytics/summary - Comprehensive analytics")
        print("   • GET /api/analytics/export/csv - CSV export")
        print("   • GET /api/analytics/department_avg - Department averages")
        print("   • GET /api/analytics/failure_rates - Subject failure rates")
        print("   • GET /api/analytics/gwa_trends?user_id=1 - GWA trends")
        print("\n🔧 To start the app manually: python app.py")
        
        # Ask if user wants to start the app now
        start_now = input("\n� Start the application now? (y/n): ").lower()
        if start_now in ['y', 'yes']:
            start_application()
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        print("📦 Try running: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main_setup()
