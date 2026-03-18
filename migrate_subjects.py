from app.database import SessionLocal
from app.models import User, SubjectGrade
import random

def migrate_student_subjects():
    db = SessionLocal()
    try:
        students = db.query(User).all()
        print(f"Checking {len(students)} students for subject count...")
        
        default_subjects = [
            "Data Structures and Algorithms", "Database Systems", "Operating Systems", 
            "Computer Organization", "Software Engineering", "Web Development", 
            "Artificial Intelligence", "Network Security"
        ]
        
        for student in students:
            # Skip admin
            if student.school_id == 'admin':
                continue
                
            current_subjects_count = db.query(SubjectGrade).filter(SubjectGrade.user_id == student.id).count()
            if current_subjects_count < 8:
                print(f"Migrating student {student.name} ({student.school_id}). Current subjects: {current_subjects_count}")
                
                # Get existing subject names to avoid duplicates
                existing_subjects = [g.subject for g in student.grades]
                
                needed = 8 - current_subjects_count
                added = 0
                for subject in default_subjects:
                    if subject not in existing_subjects and added < needed:
                        grade = round(random.uniform(1.0, 3.0), 2)
                        new_grade = SubjectGrade(
                            user_id=student.id,
                            subject=subject,
                            units=3.0,
                            grade=grade,
                            year=1,
                            semester=1
                        )
                        db.add(new_grade)
                        added += 1
                
                print(f"Added {added} subjects to {student.name}")
        
        db.commit()
        print("Migration complete!")
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_student_subjects()
