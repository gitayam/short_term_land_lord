from app import create_app, db
from app.models import User, UserRoles

app = create_app()
with app.app_context():
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role=UserRoles.ADMIN.value,
            is_admin=True
        )
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully')
    else:
        print('Admin user already exists') 