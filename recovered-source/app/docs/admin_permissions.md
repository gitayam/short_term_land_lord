# Admin Permissions System

## Overview

The application has a permissions system that uses a combination of **user roles** and an **is_admin flag**. 
This document explains how admin permissions work and how to fix issues with admin access.

## How Admin Permissions Work

1. A user can be granted admin privileges in two ways:
   - Setting the user's `role` to `UserRoles.ADMIN.value` ("admin")
   - Setting the user's `is_admin` flag to `True`

2. The `User.has_admin_role()` method checks for admin privileges using both methods:
   ```python
   def has_admin_role(self):
       """Check if the user has admin privileges."""
       # Check if the is_admin field is True or if the role is ADMIN
       return bool(self.__dict__.get('is_admin', False)) or self.role == UserRoles.ADMIN.value
   ```

3. The `is_admin` property getter and setter ensure consistency:
   ```python
   @property
   def is_admin(self):
       return self.has_admin_role()
   
   @is_admin.setter
   def is_admin(self, value):
       """Set the is_admin attribute"""
       self.__dict__['is_admin'] = value
       # Update role to admin if is_admin is set to True
       if value and self.role != UserRoles.ADMIN.value:
           self.role = UserRoles.ADMIN.value
   ```

## Admin Access to Properties

Admins can view all properties in the system, regardless of ownership. This is handled in the `property/routes.py` file:

```python
@bp.route('/<int:id>/view')
@login_required
def view(id):
    property = Property.query.get_or_404(id)
    
    # Permission check
    can_view = False
    
    # Property owners can view their own properties
    if current_user.is_property_owner and property.owner_id == current_user.id:
        can_view = True
    # Admins can view all properties
    elif current_user.has_admin_role:
        can_view = True
    # Service staff can view properties they have tasks for
    elif current_user.is_service_staff():
        # Check if the service staff has any assigned tasks for this property...
```

## Common Issues and Fixes

### Inconsistent Admin Status

A common issue is having inconsistent admin status where either:
- The `role` is set to "admin" but the `is_admin` flag is `False`
- The `is_admin` flag is `True` but the `role` is not "admin"

Both fields should be set correctly for consistent behavior across the application.

### Fix Script

The `fix_admin_role.py` script checks for these inconsistencies and fixes them:

```bash
python3 scripts/fix_admin_role.py
```

The script:
1. Finds all users with admin privileges (by role or flag)
2. Ensures both fields are set correctly
3. Reports on the changes made

### Manually Setting Admin Privileges

To manually make a user an admin, run the following in a Flask shell:

```python
from app.models import User, UserRoles
from app import db

user = User.query.filter_by(email='user@example.com').first()
user.role = UserRoles.ADMIN.value
user.is_admin = True
db.session.commit()
```

## Testing Admin Permissions

The test file `tests/test_admin_property_permissions.py` verifies that admin permissions work correctly:

```python
def test_admin_can_view_any_property(self):
    """Test that admin users can view any property"""
    with self.client as c:
        # Login as admin
        login(c, 'admin@example.com', 'adminpassword')
        
        # Try to view property owned by someone else
        response = c.get(f'/property/{self.property.id}/view', follow_redirects=True)
        
        # Check that admin can access the property view
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Property', response.data)
``` 