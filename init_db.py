import os
from app import app, db, Department, Course, User, Post, Admin

def seed():
    with app.app_context():
        reset = os.getenv('DB_RESET_ON_INIT', '').lower() in ('1', 'true', 'yes')
        if reset:
            db.drop_all()
        db.create_all()

        if not Department.query.filter_by(name='COTE').first():
            cote = Department(name='COTE')
            db.session.add(cote)
            db.session.commit()
            courses = ['Computer Science', 'Computer Engineering', 'Information Technology']
            for c in courses:
                db.session.add(Course(name=c, department_id=cote.id))
            db.session.commit()

        if not User.query.filter_by(school_id='2026001').first():
            user = User(school_id='2026001', name='Sample Student', department='COTE', course='Computer Science')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            p = Post(user_id=user.id, content='Welcome to GWAcalculator!')
            db.session.add(p)
            db.session.commit()

        admin_user = User.query.filter_by(school_id='admin').first()
        if not admin_user:
            admin_user = User(school_id='admin', name='Administrator', department='COTE', course='Administration')
            admin_user.set_password('adminpass')
            db.session.add(admin_user)
            db.session.commit()
            print('Admin user created: school_id=admin password=adminpass')
        
        if not Admin.query.filter_by(user_id=admin_user.id).first():
            db.session.add(Admin(user_id=admin_user.id))
            db.session.commit()
            print('Admin rights granted to admin user')

if __name__ == '__main__':
    seed()
