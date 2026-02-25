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
            
            # Latest COTE programs for CTU San Francisco
            courses = [
                'Bachelor of Industrial Technology - Computer Technology (BIT-CT)',
                'Bachelor of Industrial Technology - Electronics Technology (BIT-ET)',
                'Bachelor of Science in Industrial Engineering (BSIE)',
                'Bachelor of Science in Fishery (BSFi)'
            ]
            for c in courses:
                db.session.add(Course(name=c, department_id=cote.id))
            
            # Adding other Colleges for a complete SIS feel
            coed = Department(name='COED')
            db.session.add(coed)
            db.session.commit()
            coed_courses = [
                'Bachelor of Elementary Education (BEEd)',
                'Bachelor of Technology and Livelihood Education (BTLED) - Home Economics',
                'Bachelor of Secondary Education (BSEd) - Mathematics',
                'Bachelor of Secondary Education (BSEd) - Sciences'
            ]
            for c in coed_courses:
                db.session.add(Course(name=c, department_id=coed.id))

            cobm = Department(name='COBM')
            db.session.add(cobm)
            db.session.commit()
            cobm_courses = [
                'Bachelor of Science in Hospitality Management (BSHM)',
                'Bachelor of Science in Tourism Management (BSTM)'
            ]
            for c in cobm_courses:
                db.session.add(Course(name=c, department_id=cobm.id))

            db.session.commit()

        if not User.query.filter_by(school_id='2026001').first():
            user = User(school_id='2026001', name='Sample Student', department='COTE', course='Bachelor of Industrial Technology - Computer Technology (BIT-CT)')
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
