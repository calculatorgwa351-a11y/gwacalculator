#!/usr/bin/env python3
"""
FastAPI GWA Calculator Initialization Script
Generates dummy data for testing and demonstration
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, engine, User, Department, Course, Admin, SubjectGrade, Post

def generate_dummy_data():
    """Generate comprehensive dummy data for testing and analysis"""
    print("📊 Generating dummy data for FastAPI...")
    
    # Create database session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    try:
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
        
        # Generate 50 students
        departments = session.query(Department).all()
        
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
            courses = session.query(Course).filter(Course.department_id == department.id).all()
            course = random.choice(courses).name if courses else 'Undeclared'
            
            # Check if school_id already exists
            if session.query(User).filter(User.school_id == school_id).first():
                continue
            
            user = User(
                school_id=school_id,
                name=name,
                department=department.name,
                course=course
            )
            user.set_password('password123')
            session.add(user)
            session.commit()
            
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
                
                subject_grade = SubjectGrade(
                    user_id=user.id,
                    subject=subject,
                    units=units,
                    grade=grade,
                    timestamp=timestamp
                )
                session.add(subject_grade)
            
            # Generate social posts for this user (2-5 posts per user)
            num_posts = random.randint(2, 5)
            for j in range(num_posts):
                post_template = random.choice(POST_TEMPLATES)
                subject_mention = random.choice(selected_subjects) if selected_subjects else "my studies"
                content = post_template.format(subject=subject_mention)
                
                # Add timestamp variation for posts
                post_days_ago = random.randint(1, 180)
                post_timestamp = datetime.utcnow() - timedelta(days=post_days_ago)
                
                post = Post(
                    user_id=user.id,
                    content=content,
                    timestamp=post_timestamp
                )
                session.add(post)
            
            session.commit()
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
        session.rollback()
    finally:
        session.close()

def main():
    """Main initialization function"""
    print("🚀 FastAPI GWA Calculator Initialization")
    print("=" * 50)
    
    # Initialize database
    from app import init_database
    init_database()
    
    # Generate dummy data
    generate_dummy_data()
    
    print("🎉 FastAPI initialization complete!")

if __name__ == "__main__":
    main()
