#!/usr/bin/env python3
"""
Render initialization script for GWA Calculator
This script ensures database is properly initialized on Render deployment
"""

import os
from app import app, db, User, Department, Course, Admin

def init_database():
    """Initialize database with basic structure and admin user"""
    print("🗄️ Initializing database for Render...")
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Create departments and courses
            departments_data = [
                {'name': 'COTE', 'courses': ['Computer Science', 'Computer Engineering', 'Information Technology']},
                {'name': 'Business', 'courses': ['Business Administration', 'Accountancy', 'Marketing']},
                {'name': 'Liberal Arts', 'courses': ['Psychology', 'Communication Arts', 'Political Science']},
                {'name': 'Engineering', 'courses': ['Civil Engineering', 'Electrical Engineering', 'Mechanical Engineering']},
                {'name': 'Science', 'courses': ['Biology', 'Chemistry', 'Physics']}
            ]
            
            for dept_data in departments_data:
                dept = Department.query.filter_by(name=dept_data['name']).first()
                if not dept:
                    dept = Department(name=dept_data['name'])
                    db.session.add(dept)
                    db.session.commit()
                    print(f"✅ Created department: {dept.name}")
                
                for course_name in dept_data['courses']:
                    course = Course.query.filter_by(name=course_name, department_id=dept.id).first()
                    if not course:
                        course = Course(name=course_name, department_id=dept.id)
                        db.session.add(course)
                        db.session.commit()
                        print(f"✅ Created course: {course_name} in {dept.name}")
            
            # Create admin user
            admin_user = User.query.filter_by(school_id='admin').first()
            if not admin_user:
                admin_user = User(school_id='admin', name='Administrator', department='COTE', course='Administration')
                admin_user.set_password('adminpass')
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Created admin user: admin / adminpass")
                
                # Grant admin rights
                admin_record = Admin(user_id=admin_user.id)
                db.session.add(admin_record)
                db.session.commit()
                print("✅ Granted admin rights")
            else:
                print("✅ Admin user already exists")
            
            print("🗄️ Database initialization complete!")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("🎉 Render database setup successful!")
    else:
        print("💥 Render database setup failed!")
        exit(1)
