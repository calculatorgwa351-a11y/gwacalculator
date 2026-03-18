from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
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
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
