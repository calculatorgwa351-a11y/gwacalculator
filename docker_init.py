#!/usr/bin/env python3
"""
Docker initialization script for GWA Calculator
This script runs when the container starts and handles:
1. Database initialization
2. Admin user creation
3. Dummy data generation
4. Application startup
"""

import os
import sys
from app import app, db, User, Department, Course, Admin

def init_database():
    """Initialize database with basic structure and admin user"""
    print("🗄️ Initializing database...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
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

def generate_dummy_data():
    """Generate comprehensive dummy data for testing and analysis"""
    print("📊 Generating dummy data...")
    
    # Import here to avoid circular imports
    try:
        from faker import Faker
        import random
        from datetime import datetime, timedelta
        
        fake = Faker('en_PH')
        
        # Realistic Filipino names and subjects
        FIRST_NAMES = ['Juan', 'Maria', 'Jose', 'Ana', 'Pedro', 'Rosa', 'Miguel', 'Carmen', 'Antonio', 'Teresa', 
                       'Francisco', 'Elena', 'Luis', 'Sofia', 'Carlos', 'Isabella', 'Diego', 'Gabriela', 'Ricardo', 'Patricia']
        LAST_NAMES = ['Santos', 'Reyes', 'Cruz', 'Bautista', 'Aquino', 'Garcia', 'Fernandez', 'Ramos', 'Mendoza', 'Castillo',
                     'Torres', 'Navarro', 'Salazar', 'Del Rosario', 'Villanueva', 'Lopez', 'Morales', 'Rivera', 'Flores', 'Chavez']
        
        SUBJECTS = {
            'Computer Science': ['Data Structures and Algorithms', 'Computer Organization', 'Operating Systems', 'Database Systems'],
            'Computer Engineering': ['Digital Logic Design', 'Microprocessors', 'Embedded Systems', 'Computer Architecture'],
            'Information Technology': ['Systems Analysis and Design', 'IT Project Management', 'Business Process Management'],
            'Business Administration': ['Principles of Management', 'Business Finance', 'Marketing Management'],
            'Psychology': ['General Psychology', 'Developmental Psychology', 'Social Psychology']
        }
        
        with app.app_context():
            # Generate 50 students
            departments = Department.query.all()
            
            if not departments:
                print("❌ No departments found. Cannot generate dummy data.")
                return
            
            generated_count = 0
            for i in range(50):
                first_name = random.choice(FIRST_NAMES)
                last_name = random.choice(LAST_NAMES)
                name = f"{first_name} {last_name}"
                school_id = f"2024{random.randint(1000, 9999)}"
                
                department = random.choice(departments)
                courses = Course.query.filter_by(department_id=department.id).all()
                course = random.choice(courses).name if courses else 'Undeclared'
                
                # Check if school_id already exists
                if User.query.filter_by(school_id=school_id).first():
                    continue
                
                user = User(
                    school_id=school_id,
                    name=name,
                    department=department.name,
                    course=course
                )
                user.set_password('password123')
                db.session.add(user)
                db.session.commit()
                
                # Generate grades for this user
                subjects = SUBJECTS.get(course, SUBJECTS['Computer Science'])
                num_subjects = random.randint(8, 12)
                selected_subjects = random.sample(subjects, min(num_subjects, len(subjects)))
                
                for subject in selected_subjects:
                    units = random.choice([1.0, 2.0, 3.0, 4.0, 5.0])
                    # Generate realistic grades based on subject difficulty
                    if any(word in subject.lower() for word in ['introduction', 'basic', 'principles']):
                        grade = round(random.uniform(1.0, 2.5), 2)
                    elif any(word in subject.lower() for word in ['advanced', 'complex', 'design']):
                        grade = round(random.uniform(2.0, 4.0), 2)
                    else:
                        grade = round(random.uniform(1.5, 3.5), 2)
                    
                    # Add timestamp variation
                    days_ago = random.randint(1, 365)
                    timestamp = datetime.utcnow() - timedelta(days=days_ago)
                    
                    from app import SubjectGrade
                    subject_grade = SubjectGrade(
                        user_id=user.id,
                        subject=subject,
                        units=units,
                        grade=grade,
                        timestamp=timestamp
                    )
                    db.session.add(subject_grade)
                
                db.session.commit()
                generated_count += 1
                
                if generated_count % 10 == 0:
                    print(f"📊 Generated {generated_count} students...")
            
            print(f"✅ Dummy data generation complete! Generated {generated_count} students")
            print("📊 Generated realistic academic data for analysis")
            
    except ImportError as e:
        print(f"⚠️ Faker not available: {e}")
        print("📊 Skipping dummy data generation (install faker for full functionality)")
    except Exception as e:
        print(f"❌ Error generating dummy data: {e}")
        import traceback
        traceback.print_exc()

def start_application():
    """Start the Flask application"""
    print("🚀 Starting GWA Calculator application...")
    print("🌐 Application will be available at: http://localhost:5000")
    print("👤 Admin login: admin / adminpass")
    print("🎓 Student login: 2024xxxx / password123")
    print("")
    
    # Start the Flask app
    from app import app as flask_app
    flask_app.run(host='0.0.0.0', port=5000, debug=False)

def main():
    """Main initialization function"""
    print("🐳 GWA Calculator Docker Initialization")
    print("=" * 50)
    
    # Always initialize database and generate dummy data
    init_database()
    generate_dummy_data()
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main()
