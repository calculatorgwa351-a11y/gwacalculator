import sys
from app import app, db, User, Admin

if len(sys.argv) != 2:
    print('Usage: python make_admin.py <school_id>')
    sys.exit(1)

school_id = sys.argv[1]
with app.app_context():
    user = User.query.filter_by(school_id=school_id).first()
    if not user:
        print(f'User with school_id={school_id} not found')
        sys.exit(1)
    if Admin.query.filter_by(user_id=user.id).first():
        print(f'User {school_id} is already an admin')
        sys.exit(0)
    a = Admin(user_id=user.id)
    db.session.add(a)
    db.session.commit()
    print(f'User {school_id} is now an admin (user id={user.id})')