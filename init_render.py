#!/usr/bin/env python3
"""
Render initialization script for GWA Calculator
This script ensures database is properly initialized on Render deployment
"""

import os
from app import app, db, User, Department, Course, Admin
from datetime import datetime, timedelta

def init_database():
    """Initialize database with basic structure and admin user"""
    print("🗄️ Initializing database for Render...")
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Create departments and courses (8 courses total)
            departments_data = [
                {'name': 'COTE', 'courses': ['Computer Science', 'Computer Engineering']},
                {'name': 'Business', 'courses': ['Business Administration', 'Accountancy']},
                {'name': 'Liberal Arts', 'courses': ['Psychology', 'Communication Arts']},
                {'name': 'Engineering', 'courses': ['Civil Engineering', 'Electrical Engineering']}
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
            
            # Generate dummy data
            generate_dummy_data()
            
            print("🗄️ Database initialization complete!")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            db.session.rollback()
            return False

def generate_dummy_data():
    """Generate comprehensive dummy data for testing and analysis"""
    print("📊 Generating dummy data for Render...")
    
    try:
        import random
        
        # Realistic Filipino names and subjects
        FIRST_NAMES = ['Juan', 'Maria', 'Jose', 'Ana', 'Pedro', 'Rosa', 'Miguel', 'Carmen', 'Antonio', 'Teresa', 
                       'Francisco', 'Elena', 'Luis', 'Sofia', 'Carlos', 'Isabella', 'Diego', 'Gabriela', 'Ricardo', 'Patricia']
        LAST_NAMES = ['Santos', 'Reyes', 'Cruz', 'Bautista', 'Aquino', 'Garcia', 'Fernandez', 'Ramos', 'Mendoza', 'Castillo',
                     'Torres', 'Navarro', 'Salazar', 'Del Rosario', 'Villanueva', 'Lopez', 'Morales', 'Rivera', 'Flores', 'Chavez']
        
        # Social post templates
        POST_TEMPLATES = [
            "Just finished my {subject} exam! It was challenging but I think I did well. 📚",
            "Anyone else struggling with {subject}? The concepts are really complex! 😅",
            "Great day at CTU! Learned so much in {subject} class today. 👨‍🎓",
            "Study group for {subject} at the library tomorrow! Who's joining? 📖",
            "Finally understanding {subject}! The professor's teaching method really helps! 🎯",
            "Midterm season is here! {subject} is keeping me busy but I'm staying positive! 💪",
            "CTU life is amazing! Made great friends in {subject} class! 🎉",
            "Just submitted my {subject} project. Hope I get a good grade! 🤞"
        ]
        
        # Generate 30 students for Render (smaller dataset for performance)
        departments = Department.query.all()
        
        if not departments:
            print("❌ No departments found. Cannot generate dummy data.")
            return
        
        generated_count = 0
        for i in range(30):
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
            subjects = {
                'Computer Science': ['Data Structures and Algorithms', 'Computer Organization', 'Operating Systems', 'Database Systems'],
                'Computer Engineering': ['Digital Logic Design', 'Microprocessors', 'Embedded Systems', 'Computer Architecture'],
                'Business Administration': ['Principles of Management', 'Business Finance', 'Marketing Management'],
                'Accountancy': ['Financial Accounting', 'Cost Accounting', 'Auditing', 'Taxation'],
                'Psychology': ['General Psychology', 'Developmental Psychology', 'Social Psychology'],
                'Communication Arts': ['Public Speaking', 'Media Writing', 'Digital Communication', 'Journalism'],
                'Civil Engineering': ['Structural Analysis', 'Transportation Engineering', 'Geotechnical Engineering'],
                'Electrical Engineering': ['Circuit Analysis', 'Electronics', 'Power Systems', 'Control Systems']
            }
            
            course_subjects = subjects.get(course, subjects['Computer Science'])
            num_subjects = random.randint(8, 12)
            selected_subjects = random.sample(course_subjects, min(num_subjects, len(course_subjects)))
            
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
            
            # Generate social posts for this user (2-5 posts per user)
            num_posts = random.randint(2, 5)
            for j in range(num_posts):
                post_template = random.choice(POST_TEMPLATES)
                subject_mention = random.choice(selected_subjects) if selected_subjects else "my studies"
                content = post_template.format(subject=subject_mention)
                
                # Add timestamp variation for posts
                post_days_ago = random.randint(1, 180)
                post_timestamp = datetime.utcnow() - timedelta(days=post_days_ago)
                
                from app import Post
                post = Post(
                    user_id=user.id,
                    content=content,
                    timestamp=post_timestamp
                )
                db.session.add(post)
            
            db.session.commit()
            generated_count += 1
            
            if generated_count % 10 == 0:
                print(f"📊 Generated {generated_count} students...")
        
        print(f"✅ Dummy data generation complete! Generated {generated_count} students")
        print("📊 Generated realistic academic data for analysis")
        print("📊 Generated social posts for student interaction")
        
    except Exception as e:
        print(f"❌ Error generating dummy data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    success = init_database()
    if success:
        print("🎉 Render database setup successful!")
    else:
        print("💥 Render database setup failed!")
        exit(1)
