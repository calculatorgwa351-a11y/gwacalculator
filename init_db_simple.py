from app import app, db, User, Department, Course, Admin

def init():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Create admin user
        admin_user = User.query.filter_by(school_id='admin').first()
        if not admin_user:
            admin_user = User(school_id='admin', name='Administrator', department='COTE', course='Administration')
            admin_user.set_password('adminpass')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created: admin / adminpass")
            
            # Make admin
            admin_record = Admin(user_id=admin_user.id)
            db.session.add(admin_record)
            db.session.commit()
            print("Admin rights granted")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    init()
