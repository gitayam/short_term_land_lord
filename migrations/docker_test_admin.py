from app import create_app
from app.models import User, Property

app = create_app()
with app.app_context():
    admin = User.query.filter_by(role='admin').first()
    print(f'Admin exists: {admin is not None}')
    if admin:
        print(f'Admin has admin role: {admin.has_admin_role()}')
        print(f'Admin email: {admin.email}')

    prop = Property.query.first()
    print(f'Property exists: {prop is not None}')
    if prop:
        print(f'Property name: {prop.name}')
        print(f'Property owner: {prop.owner_id}')