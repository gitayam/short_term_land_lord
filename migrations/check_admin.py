from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    admin_by_role = User.query.filter_by(role='admin').first()
    admin_by_flag = User.query.filter_by(_is_admin=True).first()
    
    print('Admin by role exists:', admin_by_role is not None)
    print('Admin by flag exists:', admin_by_flag is not None)
    
    if admin_by_role:
        print(f'Admin by role: {admin_by_role.email}, has_admin_role: {admin_by_role.has_admin_role}, is_admin property: {admin_by_role.is_admin}')
    
    if admin_by_flag:
        print(f'Admin by flag: {admin_by_flag.email}, has_admin_role: {admin_by_flag.has_admin_role}, is_admin property: {admin_by_flag.is_admin}') 