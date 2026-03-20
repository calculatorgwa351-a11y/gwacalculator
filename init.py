"""
Local/dev data seeding helpers.

This module is imported by `app/main.py` during startup when there are no students.
It is also referenced by `render.yaml` as an optional one-time initialization step.
"""

from __future__ import annotations

from typing import Optional
import random

from faker import Faker

from app.database import SessionLocal
from app.models import User, SubjectGrade, Post


def generate_dummy_data(db=None, *, student_count: int = 12) -> None:
    """
    Seed a small set of students with grades and a few posts.

    - Skips seeding if student users already exist.
    - Uses password `password123` for all seeded students.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    fake = Faker("en_PH")

    try:
        existing_students = db.query(User).filter(User.school_id != "admin").count()
        if existing_students > 0:
            print(f"ℹ️ Dummy data already present ({existing_students} students). Skipping.")
            return

        departments = ["COTE", "COED", "CBM"]
        courses = {
            "COTE": ["Computer Science", "Computer Engineering"],
            "COED": ["Elementary Education", "Secondary Education"],
            "CBM": ["Business Administration", "Accountancy"]
        }

        default_subjects = [
            "Data Structures and Algorithms",
            "Database Systems",
            "Operating Systems",
            "Computer Organization",
            "Software Engineering",
            "Web Development",
            "Artificial Intelligence",
            "Network Security"
        ]

        students: list[User] = []
        base_id = 20240001
        for i in range(student_count):
            dept = random.choice(departments)
            course = random.choice(courses[dept])
            student = User(
                school_id=str(base_id + i),
                name=fake.name(),
                department=dept,
                course=course
            )
            student.set_password("password123")
            db.add(student)
            students.append(student)

        db.commit()
        for s in students:
            db.refresh(s)

        # Grades
        for s in students:
            for subject in default_subjects:
                grade = round(random.uniform(1.0, 3.0), 2)
                db.add(
                    SubjectGrade(
                        user_id=s.id,
                        subject=subject,
                        units=3.0,
                        grade=grade,
                        year=random.choice([1, 2, 3, 4]),
                        semester=random.choice([1, 2])
                    )
                )

        # A few posts
        for s in random.sample(students, k=min(5, len(students))):
            db.add(
                Post(
                    user_id=s.id,
                    content=fake.sentence(nb_words=14)
                )
            )

        db.commit()
        print(f"✅ Generated dummy data: {len(students)} students")
    finally:
        if close_db:
            db.close()

