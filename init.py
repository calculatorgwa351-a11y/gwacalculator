"""
Local/dev data seeding helpers.

This module is imported by `app/main.py` during startup and can also be used
from admin seed endpoints.
"""

from __future__ import annotations

import random

from faker import Faker

from app.database import SessionLocal
from app.models import Comment, Post, SubjectGrade, User


DEFAULT_SUBJECTS = [
    "Data Structures and Algorithms",
    "Database Systems",
    "Operating Systems",
    "Computer Organization",
    "Software Engineering",
    "Web Development",
    "Artificial Intelligence",
    "Network Security",
]

FILIPINO_FIRST_NAMES = [
    "Juan",
    "Jose",
    "Andres",
    "Miguel",
    "Ramon",
    "Paolo",
    "Carlo",
    "Angelo",
    "Gabriel",
    "Mark",
    "Maria",
    "Juana",
    "Ana",
    "Angelica",
    "Catherine",
    "Ma. Teresa",
    "Patricia",
    "Kimberly",
    "Lovely",
    "Jasmine",
    "Erika",
    "Bea",
    "Katrina",
    "Aira",
    "Kristine",
    "Jhon",
    "John Paul",
    "Mary Grace",
    "Princess",
    "Reynaldo",
]
FILIPINO_LAST_NAMES = [
    "Dela Cruz",
    "Santos",
    "Reyes",
    "Garcia",
    "Mendoza",
    "Bautista",
    "Ocampo",
    "Aquino",
    "Castillo",
    "Flores",
    "Ramos",
    "Gonzales",
    "Torres",
    "Navarro",
    "Villanueva",
    "Cruz",
    "Lopez",
    "Rivera",
    "Hernandez",
    "Perez",
    "Domingo",
    "Padilla",
    "Salazar",
    "Santiago",
    "Morales",
    "Fernandez",
    "Diaz",
    "Castro",
    "Valdez",
    "Del Rosario",
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
    updated = 0
    students = db.query(User).filter(User.school_id != "admin").all()
    if not students:
        return 0

    for student in students:
        if not student.school_id or not student.school_id.startswith(school_id_prefix):
            continue

        target = filipino_full_name_for_school_id(student.school_id)
        if student.name and any(student.name.strip().endswith(last) for last in FILIPINO_LAST_NAMES):
            continue

        if student.name != target:
            student.name = target
            updated += 1

    if updated:
        db.commit()
        print(f"Updated {updated} student names to Filipino style")

    return updated


def ensure_grades_for_all_students(db, *, min_subjects: int = 8) -> int:
    inserted = 0
    students = db.query(User).filter(User.school_id != "admin").all()
    if not students:
        return 0

    for student in students:
        existing_count = db.query(SubjectGrade).filter(SubjectGrade.user_id == student.id).count()
        needed = max(0, min_subjects - existing_count)
        if needed == 0:
            continue

        for index in range(needed):
            subject = DEFAULT_SUBJECTS[(existing_count + index) % len(DEFAULT_SUBJECTS)]
            subject_name = (
                subject
                if existing_count + index < len(DEFAULT_SUBJECTS)
                else f"{subject} ({existing_count + index + 1})"
            )
            grade = round(random.uniform(1.0, 3.0), 2)
            db.add(
                SubjectGrade(
                    user_id=student.id,
                    subject=subject_name,
                    units=3.0,
                    grade=grade,
                    year=random.choice([1, 2, 3, 4]),
                    semester=random.choice([1, 2]),
                )
            )
            inserted += 1

    if inserted:
        db.commit()
        print(f"Seeded {inserted} grades across students")
    return inserted


def generate_dummy_data(
    db=None,
    *,
    student_count: int = 12,
    add_if_existing: bool = False,
    base_school_id: int = 20240001,
) -> dict:
    """
    Seed students with grades and sample posts.

    - By default, skips seeding if student users already exist.
    - With `add_if_existing=True`, inserts only missing demo users.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        fake = Faker("en_PH")
    except Exception:
        fake = Faker()

    try:
        existing_students = db.query(User).filter(User.school_id != "admin").count()
        if existing_students > 0 and not add_if_existing:
            print(f"Dummy data already present ({existing_students} students). Skipping.")
            return {
                "created_students": 0,
                "existing_students": existing_students,
                "seeded_grades": 0,
                "seeded_posts": 0,
                "seeded_comments": 0,
                "skipped_existing_demo": 0,
            }

        departments = ["COTE", "COED", "CBM"]
        courses = {
            "COTE": ["Computer Science", "Computer Engineering"],
            "COED": ["Elementary Education", "Secondary Education"],
            "CBM": ["Business Administration", "Accountancy"],
        }

        existing_by_school_id = {
            user.school_id: user for user in db.query(User).filter(User.school_id != "admin").all()
        }

        new_students: list[User] = []
        skipped_existing_demo = 0
        for index in range(student_count):
            school_id = str(base_school_id + index)
            if school_id in existing_by_school_id:
                skipped_existing_demo += 1
                continue

            department = random.choice(departments)
            course = random.choice(courses[department])
            student = User(
                school_id=school_id,
                name=filipino_full_name_for_school_id(school_id),
                department=department,
                course=course,
            )
            student.set_password("password123")
            db.add(student)
            new_students.append(student)

        if not new_students:
            print("Demo students already exist. No new users inserted.")
            return {
                "created_students": 0,
                "existing_students": existing_students,
                "seeded_grades": 0,
                "seeded_posts": 0,
                "seeded_comments": 0,
                "skipped_existing_demo": skipped_existing_demo,
            }

        db.commit()
        for student in new_students:
            db.refresh(student)

        seeded_grades = 0
        for student in new_students:
            for subject in DEFAULT_SUBJECTS:
                grade = round(random.uniform(1.0, 3.0), 2)
                db.add(
                    SubjectGrade(
                        user_id=student.id,
                        subject=subject,
                        units=3.0,
                        grade=grade,
                        year=random.choice([1, 2, 3, 4]),
                        semester=random.choice([1, 2]),
                    )
                )
                seeded_grades += 1

        seeded_posts = 0
        seeded_comments = 0
        for student in random.sample(new_students, k=min(5, len(new_students))):
            post = Post(user_id=student.id, content=fake.sentence(nb_words=14))
            db.add(post)
            db.flush()
            seeded_posts += 1

            commenters = random.sample(new_students, k=min(3, len(new_students)))
            for commenter in commenters:
                comment = Comment(post_id=post.id, user_id=commenter.id, content=fake.sentence(nb_words=10))
                db.add(comment)
                db.flush()
                seeded_comments += 1

                if random.choice([True, False]):
                    db.add(
                        Comment(
                            post_id=post.id,
                            user_id=commenter.id,
                            parent_comment_id=comment.id,
                            content=fake.sentence(nb_words=6),
                        )
                    )
                    seeded_comments += 1

        db.commit()
        created_students = len(new_students)
        print(f"Generated dummy data: {created_students} students")
        return {
            "created_students": created_students,
            "existing_students": existing_students,
            "seeded_grades": seeded_grades,
            "seeded_posts": seeded_posts,
            "seeded_comments": seeded_comments,
            "skipped_existing_demo": skipped_existing_demo,
        }
    finally:
        if close_db:
            db.close()
