from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import Base

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    password_hash = Column(String(128), nullable=False)
    department = Column(String(64))
    course = Column(String(128))
    
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    grades = relationship("SubjectGrade", back_populates="student", cascade="all, delete-orphan")
    
    @staticmethod
    def _password_for_hashing(password) -> str:
        """
        bcrypt only supports up to 72 bytes of input.
        For longer passwords, pre-hash with SHA-256 to avoid runtime errors and
        avoid bcrypt's silent truncation behavior.
        """
        if password is None:
            return ""

        if isinstance(password, bytes):
            raw = password
            text = password.decode("utf-8", errors="ignore")
        else:
            text = str(password)
            raw = text.encode("utf-8")

        if len(raw) <= 72:
            return text

        digest = hashlib.sha256(raw).hexdigest()
        return f"sha256:{digest}"

    def set_password(self, password):
        # Use Werkzeug PBKDF2 (works well cross-platform and avoids bcrypt backend issues)
        normalized = self._password_for_hashing(password)
        self.password_hash = generate_password_hash(normalized, method="pbkdf2:sha256", salt_length=16)
    
    def check_password(self, password):
        if not self.password_hash:
            return False
            
        # Werkzeug hashes usually start with pbkdf2:
        if self.password_hash.startswith('pbkdf2:sha256:'):
            return check_password_hash(self.password_hash, self._password_for_hashing(password))
            
        try:
            # Backward-compat: if a bcrypt hash exists in the DB, try verifying with bcrypt directly.
            if self.password_hash.startswith(("$2a$", "$2b$", "$2y$")):
                import bcrypt

                candidate = self._password_for_hashing(password).encode("utf-8")
                return bcrypt.checkpw(candidate, self.password_hash.encode("utf-8"))
        except Exception:
            return False

        return False

class Department(Base):
    __tablename__ = 'department'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)
    
    courses = relationship("Course", back_populates="department")

class Course(Base):
    __tablename__ = 'course'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    department_id = Column(Integer, ForeignKey('department.id'))
    
    department = relationship("Department", back_populates="courses")

class Post(Base):
    __tablename__ = 'post'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    author = relationship("User", back_populates="posts")
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

class Reaction(Base):
    __tablename__ = 'reaction'
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    type = Column(String(32), default='like')
    
    post = relationship("Post", back_populates="reactions")

class Comment(Base):
    __tablename__ = 'comment'
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    post = relationship("Post", back_populates="comments")
    author = relationship("User")

class SubjectGrade(Base):
    __tablename__ = 'subject_grade'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    subject = Column(String(128), nullable=False)
    units = Column(Float, default=3.0)
    grade = Column(Float, nullable=False)
    year = Column(Integer, default=1)
    semester = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    student = relationship("User", back_populates="grades")
    
    def is_failed(self):
        return self.grade is not None and self.grade > 3.0

class Admin(Base):
    __tablename__ = 'admin'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), unique=True)
    
    user = relationship("User")
