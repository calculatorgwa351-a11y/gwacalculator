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
from app.models import User, SubjectGrade, Post, Comment


DEFAULT_SUBJECTS = [
    "Data Structures and Algorithms",
    "Database Systems",
    "Operating Systems",
    "Computer Organization",
    "Software Engineering",
    "Web Development",
    "Artificial Intelligence",
    "Network Security"
]

# Prefer Filipino-looking names for seeded/dummy students.
FILIPINO_FIRST_NAMES = [
    "Juan", "Jose", "Andres", "Miguel", "Ramon", "Paolo", "Carlo", "Angelo", "Gabriel", "Mark",
    "Maria", "Juana", "Ana", "Angelica", "Catherine", "Ma. Teresa", "Patricia", "Kimberly", "Lovely", "Jasmine",
    "Erika", "Bea", "Katrina", "Aira", "Kristine", "Jhon", "John Paul", "Mary Grace", "Princess", "Reynaldo"
]
FILIPINO_LAST_NAMES = [
    "Dela Cruz", "Santos", "Reyes", "Garcia", "Mendoza", "Bautista", "Ocampo", "Aquino", "Castillo", "Flores",
    "Ramos", "Gonzales", "Torres", "Navarro", "Villanueva", "Cruz", "Lopez", "Rivera", "Hernandez", "Perez",
    "Domingo", "Padilla", "Salazar", "Santiago", "Morales", "Fernandez", "Diaz", "Castro", "Valdez", "Del Rosario"
]


def _deterministic_index(value: str, modulo: int) -> int:
    import hashlib

    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % modulo


def filipino_full_name_for_school_id(school_id: str) -> str:
    first = FILIPINO_FIRST_NAMES[_deterministic_index(f"{school_id}:first", len(FILIPINO_FIRST_NAMES))]
    last = FILIPINO_LAST_NAMES[_deterministic_index(f"{school_id}:last", len(FILIPINO_LAST_NAMES))]
    return f"{first} {last}"


def assign_filipino_names_to_students(db, *, school_id_prefix: str = "2024") -> int:
    """
    Update existing students (non-admin) to Filipino-style names.

    This is intended for dummy/seeded student accounts (e.g. school IDs like 2024xxxx).
    Returns the number of users updated.
    """
    updated = 0
    students = db.query(User).filter(User.school_id != "admin").all()
    if not students:
        return 0

    for s in students:
        if not s.school_id or not s.school_id.startswith(school_id_prefix):
            continue

        target = filipino_full_name_for_school_id(s.school_id)

        # If already Filipino-ish, keep it.
        if s.name and any(s.name.strip().endswith(last) for last in FILIPINO_LAST_NAMES):
            continue

        if s.name != target:
            s.name = target
            updated += 1

    if updated:
        db.commit()
        print(f"✅ Updated {updated} student names to Filipino style")

    return updated


def ensure_grades_for_all_students(db, *, min_subjects: int = 8) -> int:
    """
    Ensure every non-admin student has at least `min_subjects` SubjectGrade rows.
    Returns the number of grades inserted.
    """
    inserted = 0
    students = db.query(User).filter(User.school_id != "admin").all()
    if not students:
        return 0

    for s in students:
        existing_count = db.query(SubjectGrade).filter(SubjectGrade.user_id == s.id).count()
        needed = max(0, min_subjects - existing_count)
        if needed == 0:
            continue

        # Make subject names unique per student to avoid duplicate UI rows.
        for i in range(needed):
            subject = DEFAULT_SUBJECTS[(existing_count + i) % len(DEFAULT_SUBJECTS)]
            subject_name = subject if existing_count + i < len(DEFAULT_SUBJECTS) else f"{subject} ({existing_count + i + 1})"
            grade = round(random.uniform(1.0, 3.0), 2)
            db.add(
                SubjectGrade(
                    user_id=s.id,
                    subject=subject_name,
                    units=3.0,
                    grade=grade,
                    year=random.choice([1, 2, 3, 4]),
                    semester=random.choice([1, 2])
                )
            )
            inserted += 1

    if inserted:
        db.commit()
        print(f"✅ Seeded {inserted} grades across students")
    return inserted


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

    # Keep Faker as a fallback if lists are edited down to empty.
    try:
        fake = Faker("en_PH")
    except Exception:
        fake = Faker()

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

        students: list[User] = []
        base_id = 20240001
        for i in range(student_count):
            dept = random.choice(departments)
            course = random.choice(courses[dept])
            student = User(
                school_id=str(base_id + i),
                name=filipino_full_name_for_school_id(str(base_id + i)) if FILIPINO_FIRST_NAMES and FILIPINO_LAST_NAMES else fake.name(),
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
            for subject in DEFAULT_SUBJECTS:
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
            post = Post(
                user_id=s.id,
                content=fake.sentence(nb_words=14)
            )
            db.add(post)
            db.flush()

            # Add comments to the post
            commenters = random.sample(students, k=min(3, len(students)))
            for commenter in commenters:
                comment = Comment(
                    post_id=post.id,
                    user_id=commenter.id,
                    content=fake.sentence(nb_words=10)
                )
                db.add(comment)
                db.flush()
                if random.choice([True, False]):
                    db.add(
                        Comment(
                            post_id=post.id,
                            user_id=commenter.id,
                            parent_comment_id=comment.id,
                            content=fake.sentence(nb_words=6)
                        )
                    )

        db.commit()
        print(f"✅ Generated dummy data: {len(students)} students")
    finally:
        if close_db:
            db.close()
