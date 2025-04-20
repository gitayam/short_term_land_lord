from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    admin_role = User.query.filter_by(role='admin').first()
    is_admin_flag = User.query.filter_by(is_admin=True).first()
    print(f'Admin by role: {admin_role is not None}')
    print(f'Admin by flag: {is_admin_flag is not None}')
    if admin_role:
        print(f'Admin role user admin check: {admin_role.has_admin_role()}')
        print(f'Admin email: {admin_role.email}')
    if is_admin_flag:
        print(f'Admin flag user admin check: {is_admin_flag.has_admin_role()}')
        print(f'Admin flag email: {is_admin_flag.email}') 