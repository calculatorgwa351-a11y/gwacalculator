
import json
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from urllib.parse import urlparse, urljoin
import logging

app = Flask(__name__)
app.config.from_object(Config)

# Rate Limiter setup
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# CORS setup
CORS(app, origins=app.config.get('CORS_ALLOWED_ORIGINS', '*'))

db = SQLAlchemy(app)

# --- Utils ---
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
    return dict(current_user=user)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(64))
    course = db.Column(db.String(128))

    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")
    grades = db.relationship('SubjectGrade', backref='student', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    courses = db.relationship('Course', backref='department', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    reactions = db.relationship('Reaction', backref='post', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String(32), default='like')  # like, love, wow, etc.

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='user_comments', lazy=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SubjectGrade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(128))
    units = db.Column(db.Float, default=3.0)
    grade = db.Column(db.Float)
    year = db.Column(db.Integer, default=1)  # 1st, 2nd, 3rd, 4th
    semester = db.Column(db.Integer, default=1)  # 1st, 2nd, Summer
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def is_failed(self):
        return self.grade is not None and self.grade > 3.0

# Simple Admin mapping table so we don't need to alter User schema in-place
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

# expose model classes to Jinja templates for convenience
app.jinja_env.globals['User'] = User
app.jinja_env.globals['Department'] = Department
app.jinja_env.globals['Course'] = Course
app.jinja_env.globals['Admin'] = Admin

# --- Auth helpers ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


from sqlalchemy.exc import OperationalError

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        user = db.session.get(User, session['user_id'])
        if not user:
            return redirect(url_for('login', next=request.url))
        is_admin = Admin.query.filter_by(user_id=user.id).first()
        if not is_admin:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Utility functions ---
def compute_gwa_for_user(user_id):
    grades = SubjectGrade.query.filter_by(user_id=user_id).all()
    total_units = sum(g.units for g in grades if g.units is not None and g.grade is not None)
    if total_units == 0:
        return None
    total = sum(g.units * g.grade for g in grades if g.units is not None and g.grade is not None)
    return round(total / total_units, 3)

def analyze_latin_honors(user_id):
    """
    Analyzes Latin Honors eligibility based on CTU standards:
    - Summa: 1.00 - 1.20
    - Magna: 1.21 - 1.45
    - Cum Laude: 1.46 - 1.75
    - Requirements: No failing grades (>3.0), no grade below 2.5, full load per semester
    """
    grades = SubjectGrade.query.filter_by(user_id=user_id).all()
    if not grades:
        return {"eligible": False, "reason": "No grades recorded", "title": None}

    # Group by semester to check load (CTU regular load is typically 18+ units, or all prescribed)
    # For simplicity, we'll check if any major semester has < 15 units
    semester_loads = {}
    total_units = 0
    total_weighted_grade = 0
    has_failed = False
    has_below_2_5 = False

    for g in grades:
        if g.grade is None or g.units is None:
            continue

        # Exclude NSTP/ROTC from GWA
        subj_upper = (g.subject or "").upper()
        if "NSTP" in subj_upper or "ROTC" in subj_upper:
            continue

        total_units += g.units
        total_weighted_grade += (g.units * g.grade)

        # Track semester loads (excluding summer for load check)
        if g.semester != 3: # 3 is Summer
            key = f"{g.year}-{g.semester}"
            semester_loads[key] = semester_loads.get(key, 0) + g.units

        if g.grade > 3.0:
            has_failed = True
        if g.grade > 2.5:
            has_below_2_5 = True

    # CTU Residency & Load Check: Must maintain full load
    # Normal semester load is 15+ units. Irregular if any sem < 15 units.
    underloaded = any(load < 15 for load in semester_loads.values()) if semester_loads else False

    if total_units == 0:
        return {"eligible": False, "reason": "No valid academic units", "title": None, "status": "Regular"}

    gwa = round(total_weighted_grade / total_units, 3)
    status = "Irregular" if underloaded else "Regular"

    if has_failed:
        return {"eligible": False, "reason": "Has failing grades (>3.0)", "title": None, "gwa": gwa, "status": status}
    
    if has_below_2_5:
        return {"eligible": False, "reason": "Has grades below 2.50", "title": None, "gwa": gwa, "status": status}

    if underloaded:
         return {"eligible": False, "reason": "Underloaded in one or more semesters", "title": None, "gwa": gwa, "status": "Irregular"}

    title = None
    if 1.00 <= gwa <= 1.20:
        title = "Summa Cum Laude"
    elif 1.21 <= gwa <= 1.45:
        title = "Magna Cum Laude"
    elif 1.46 <= gwa <= 1.75:
        title = "Cum Laude"

    if title:
        return {"eligible": True, "reason": "Meets all CTU academic criteria", "title": title, "gwa": gwa, "status": status}
    else:
        return {"eligible": False, "reason": "GWA does not meet honors cutoff", "title": None, "gwa": gwa, "status": status}

# --- Error Handlers ---
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Too many requests. Please try again later."), 429

@app.errorhandler(404)
def not_found_error(error):
    return render_template('login.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logging.error(f"Server Error: {error}")
    return render_template('login.html', error="An internal server error occurred. Our team has been notified."), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled Exception: {e}")
    return jsonify(error="An unexpected error occurred."), 500

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    next_url = request.args.get('next')
    if request.method == 'POST':
        school_id = request.form['school_id']
        password = request.form['password']
        user = User.query.filter_by(school_id=school_id).first()
        if user and user.check_password(password):
            session.permanent = True
            session['user_id'] = user.id
            if next_url and is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    if request.method == 'POST':
        school_id = request.form['school_id']
        name = request.form['name']
        password = request.form['password']
        department = request.form['department']
        course = request.form['course']
        if User.query.filter_by(school_id=school_id).first():
            return render_template('register.html', error='School ID already registered')
        u = User(school_id=school_id, name=name, department=department, course=course)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        session.permanent = True
        session['user_id'] = u.id
        return redirect(url_for('dashboard'))
    departments = Department.query.all()
    return render_template('register.html', departments=departments)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    departments = Department.query.all()
    posts = Post.query.order_by(Post.timestamp.desc()).limit(50).all()
    grades = SubjectGrade.query.filter_by(user_id=user.id).all()
    gwa = compute_gwa_for_user(user.id)
    honors = analyze_latin_honors(user.id)
    return render_template('dashboard.html', user=user, departments=departments, posts=posts, grades=grades, gwa=gwa, honors=honors)

# API: posts
@app.route('/api/posts', methods=['GET','POST'])
@login_required
def api_posts():
    if request.method == 'GET':
        posts = Post.query.order_by(Post.timestamp.desc()).limit(100).all()
        data = []
        for p in posts:
            # build reaction summary by type
            r_summary = {}
            for r in p.reactions:
                r_summary[r.type] = r_summary.get(r.type, 0) + 1
            data.append({
                'id': p.id,
                'content': p.content,
                'author': p.author.name,
                'author_id': p.author.id,
                'timestamp': p.timestamp.isoformat(),
                'reactions': r_summary,
                'comments': [{'id': c.id, 'user': (c.author.name if c.author else "Unknown"), 'content': c.content, 'timestamp': c.timestamp.isoformat()} for c in p.comments]
            })
        return jsonify(data)

    # POST create
    payload = request.get_json()
    content = payload.get('content','').strip()
    if not content:
        return jsonify({'error':'Empty post'}), 400
    p = Post(user_id=session['user_id'], content=content)
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': p.id, 'content': p.content, 'author': User.query.get(p.user_id).name, 'timestamp': p.timestamp.isoformat()})

@app.route('/api/posts/<int:post_id>/react', methods=['POST'])
@login_required
def api_react(post_id):
    p = Post.query.get_or_404(post_id)
    user_id = session['user_id']
    payload = request.get_json() or {}
    rtype = payload.get('type','like')
    # allow only a single reaction per user per post; replace existing reaction if different
    existing = Reaction.query.filter_by(post_id=post_id, user_id=user_id).first()
    if existing:
        if existing.type == rtype:
            db.session.delete(existing)
            db.session.commit()
            # re-query counts
            r_summary = {}
            for r in p.reactions:
                r_summary[r.type] = r_summary.get(r.type, 0) + 1
            return jsonify({'status':'removed','reactions': r_summary})
        else:
            # change type
            existing.type = rtype
            db.session.commit()
            r_summary = {}
            for r in p.reactions:
                r_summary[r.type] = r_summary.get(r.type, 0) + 1
            return jsonify({'status':'changed','reactions': r_summary})
    r = Reaction(post_id=post_id, user_id=user_id, type=rtype)
    db.session.add(r)
    db.session.commit()
    r_summary = {}
    for r in p.reactions:
        r_summary[r.type] = r_summary.get(r.type, 0) + 1
    return jsonify({'status':'added','reactions': r_summary})

@app.route('/api/posts/<int:post_id>/comments', methods=['GET','POST'])
@login_required
def api_comments(post_id):
    p = Post.query.get_or_404(post_id)
    if request.method == 'GET':
        return jsonify([{'id': c.id, 'user': User.query.get(c.user_id).name, 'content': c.content, 'timestamp': c.timestamp.isoformat()} for c in p.comments])
    payload = request.get_json()
    content = payload.get('content','').strip()
    if not content:
        return jsonify({'error':'Empty comment'}), 400
    c = Comment(post_id=post_id, user_id=session['user_id'], content=content)
    db.session.add(c)
    db.session.commit()
    return jsonify({'id': c.id, 'user': User.query.get(c.user_id).name, 'content': c.content, 'timestamp': c.timestamp.isoformat()})

# API: grades
@app.route('/api/grades', methods=['GET','POST'])
@login_required
def api_grades():
    user_id = session['user_id']
    if request.method == 'GET':
        grades = SubjectGrade.query.filter_by(user_id=user_id).all()
        return jsonify([{'id': g.id, 'subject': g.subject, 'units': g.units, 'grade': g.grade, 'year': g.year, 'semester': g.semester, 'failed': g.is_failed()} for g in grades])
    payload = request.get_json()
    subject = payload.get('subject','').strip()
    try:
        units = float(payload.get('units',3.0))
        grade = float(payload.get('grade'))
        year = int(payload.get('year', 1))
        semester = int(payload.get('semester', 1))
    except (TypeError, ValueError):
        return jsonify({'error':'Units, grade, year, and semester must be numeric'}), 400
    # validate
    if not subject:
        return jsonify({'error':'Subject required'}), 400
    if not (1.0 <= grade <= 5.0):
        return jsonify({'error':'Grade must be between 1.0 (highest) and 5.0 (lowest)'}), 400
    if units <= 0:
        return jsonify({'error':'Units must be positive'}), 400
    # Auto-post achievement if GWA improved significantly
    old_gwa = compute_gwa_for_user(user_id)
    
    g = SubjectGrade(user_id=user_id, subject=subject, units=units, grade=grade, year=year, semester=semester)
    db.session.add(g)
    db.session.commit()
    
    gwa = compute_gwa_for_user(user_id)
    
    if gwa and (old_gwa is None or gwa < old_gwa) and gwa <= 2.0:
        achievement = Post(
            user_id=user_id, 
            content=f"🎉 ACHIEVEMENT: Just updated my grades and my GWA is now {gwa}! Target: Latin Honors! 🎓 #CTU #GWAcalculator"
        )
        db.session.add(achievement)
        db.session.commit()

    # compute failed subjects
    failed = SubjectGrade.query.filter(SubjectGrade.user_id==user_id, SubjectGrade.grade>3.0).count()
    return jsonify({'id': g.id, 'subject': g.subject, 'units': g.units, 'grade': g.grade, 'year': g.year, 'semester': g.semester, 'failed': g.is_failed(), 'gwa': gwa, 'failed_count': failed})

# edit existing grade
@app.route('/api/grades/<int:grade_id>', methods=['PUT'])
@login_required
def api_update_grade(grade_id):
    u_id = session['user_id']
    g = SubjectGrade.query.filter_by(id=grade_id, user_id=u_id).first_or_404()
    payload = request.get_json() or {}
    subject = payload.get('subject', g.subject).strip()
    try:
        units = float(payload.get('units', g.units))
        grade_val = float(payload.get('grade', g.grade))
    except (TypeError, ValueError):
        return jsonify({'error':'Units and grade must be numeric'}), 400
    # validate
    if not subject:
        return jsonify({'error':'Subject required'}), 400
    if not (1.0 <= grade_val <= 5.0):
        return jsonify({'error':'Grade must be between 1.0 (highest) and 5.0 (lowest)'}), 400
    if units <= 0:
        return jsonify({'error':'Units must be positive'}), 400
    g.subject = subject
    g.units = units
    g.grade = grade_val
    g.year = int(payload.get('year', g.year))
    g.semester = int(payload.get('semester', g.semester))
    g.timestamp = datetime.utcnow()
    db.session.commit()
    gwa = compute_gwa_for_user(u_id)
    failed = SubjectGrade.query.filter(SubjectGrade.user_id==u_id, SubjectGrade.grade>3.0).count()
    return jsonify({'id': g.id, 'subject': g.subject, 'units': g.units, 'grade': g.grade, 'failed': g.is_failed(), 'gwa': gwa, 'failed_count': failed})

# API: analytics
@app.route('/api/analytics', methods=['GET'])
@login_required
def api_analytics():
    # summary analytics
    users = User.query.all()
    gwas = []
    total_subjects = 0
    failed_subjects = 0
    for u in users:
        grades = SubjectGrade.query.filter_by(user_id=u.id).all()
        total_subjects += len(grades)
        failed_subjects += sum(1 for g in grades if g.grade>3.0)
        gwa = compute_gwa_for_user(u.id)
        if gwa is not None:
            gwas.append(gwa)
    avg_gwa = round(sum(gwas)/len(gwas),3) if gwas else None
    fail_rate = (failed_subjects/total_subjects) if total_subjects>0 else None
    return jsonify({'average_gwa': avg_gwa, 'failure_rate': fail_rate})

@app.route('/api/analytics/department_avg', methods=['GET'])
@login_required
def api_dept_avg():
    # average GWA per department
    depts = Department.query.all()
    out = {}
    for d in depts:
        dept_users = User.query.filter_by(department=d.name).all()
        gwas = []
        for u in dept_users:
            gwa = compute_gwa_for_user(u.id)
            if gwa is not None:
                gwas.append(gwa)
        out[d.name] = round(sum(gwas)/len(gwas),3) if gwas else None
    return jsonify(out)

@app.route('/api/analytics/failure_rates', methods=['GET'])
@login_required
def api_failure_rates():
    # failure rates per subject name
    subjects = db.session.query(SubjectGrade.subject).distinct().all()
    out = {}
    for s in subjects:
        name = s[0]
        total = SubjectGrade.query.filter_by(subject=name).count()
        failed = SubjectGrade.query.filter_by(subject=name).filter(SubjectGrade.grade>3.0).count()
        out[name] = {'total': total, 'failed': failed, 'failure_rate': round((failed/total),3) if total>0 else None}
    return jsonify(out)

@app.route('/api/analytics/gwa_trends', methods=['GET'])
@login_required
def api_gwa_trends():
    # return GWA over time for a user (pass user_id as param) as list of {timestamp, gwa}
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error':'user_id query parameter required (e.g. ?user_id=1)'}), 400
    grades = SubjectGrade.query.filter_by(user_id=user_id).order_by(SubjectGrade.timestamp.asc()).all()
    timeline = []
    # accumulate and compute GWA at each grade timestamp
    accumulated = []
    for g in grades:
        accumulated.append(g)
        total_units = sum(item.units for item in accumulated)
        total_points = sum(item.units * item.grade for item in accumulated)
        gwa = round(total_points/total_units,3) if total_units>0 else None
        timeline.append({'timestamp': g.timestamp.isoformat(), 'gwa': gwa})
    return jsonify({'user_id': user_id, 'timeline': timeline})

# -------------------- Admin routes & APIs --------------------
@app.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin.html')

@app.route('/admin-auth', methods=['POST'])
@limiter.limit("5 per minute")
def admin_auth():
    data = request.get_json() or {}
    school_id = data.get('school_id')
    password = data.get('password')
    if not school_id or not password:
        return jsonify({'error':'Missing credentials'}), 400
    user = User.query.filter_by(school_id=school_id).first()
    if not user or not user.check_password(password):
        return jsonify({'error':'Invalid credentials'}), 401
    # ensure admin mapping exists
    try:
        is_admin = Admin.query.filter_by(user_id=user.id).first()
    except Exception:
        is_admin = None
    if not is_admin:
        return jsonify({'error':'Not an admin'}), 403
    session['user_id'] = user.id
    return jsonify({'redirect': url_for('admin_panel')})

@app.route('/api/admin/students', methods=['GET', 'POST'])
@admin_required
def api_admin_students():
    if request.method == 'GET':
        users = User.query.all()
        out = []
        for u in users:
            grades = SubjectGrade.query.filter_by(user_id=u.id).all()
            gwa = compute_gwa_for_user(u.id)
            failed = sum(1 for g in grades if g.grade>3.0)
            posts_count = Post.query.filter_by(user_id=u.id).count()
            out.append({'id': u.id, 'school_id': u.school_id, 'name': u.name, 'department': u.department, 'course': u.course, 'gwa': gwa, 'failed_count': failed, 'subjects': len(grades), 'posts': posts_count})
        return jsonify(out)

    # POST create student
    data = request.get_json() or {}
    school_id = data.get('school_id')
    name = data.get('name')
    password = data.get('password')
    department = data.get('department')
    course = data.get('course')
    
    if not all([school_id, name, password]):
        return jsonify({'error': 'School ID, name, and password are required'}), 400
    
    if User.query.filter_by(school_id=school_id).first():
        return jsonify({'error': 'School ID already exists'}), 400
        
    u = User(school_id=school_id, name=name, department=department, course=course)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return jsonify({'id': u.id, 'school_id': u.school_id, 'name': u.name})

@app.route('/api/admin/student/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def api_admin_student(user_id):
    u = User.query.get_or_404(user_id)
    
    if request.method == 'GET':
        grades = SubjectGrade.query.filter_by(user_id=u.id).all()
        posts = Post.query.filter_by(user_id=u.id).order_by(Post.timestamp.desc()).all()
        return jsonify({
            'id': u.id, 'school_id': u.school_id, 'name': u.name, 'department': u.department, 'course': u.course,
            'grades': [{'subject': g.subject, 'units': g.units, 'grade': g.grade, 'failed': g.is_failed()} for g in grades],
            'posts': [{'id': p.id, 'content': p.content, 'timestamp': p.timestamp.isoformat()} for p in posts],
            'gwa': compute_gwa_for_user(u.id)
        })

    if request.method == 'PUT':
        data = request.get_json() or {}
        u.name = data.get('name', u.name)
        u.school_id = data.get('school_id', u.school_id)
        u.department = data.get('department', u.department)
        u.course = data.get('course', u.course)
        
        password = data.get('password')
        if password:
            u.set_password(password)
            
        db.session.commit()
        return jsonify({'status': 'updated'})

    if request.method == 'DELETE':
        # Don't allow deleting yourself if you're the admin
        if u.id == session.get('user_id'):
            return jsonify({'error': 'Cannot delete your own account'}), 400
            
        # Is this user also in the Admin table?
        admin_rec = Admin.query.filter_by(user_id=u.id).first()
        if admin_rec:
            db.session.delete(admin_rec)
            
        db.session.delete(u)
        db.session.commit()
        return jsonify({'status': 'deleted'})

 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', False), threaded=True)
