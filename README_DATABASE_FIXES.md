# Database Compatibility Fixes

This document explains the database compatibility fixes implemented to ensure the application works correctly with both PostgreSQL and SQLite databases.

## Issues Addressed

1. **Table Name Discrepancy**: The User model is defined with `__tablename__ = 'user'` but in PostgreSQL it's named 'users'.
2. **Enum Value Format Mismatch**: PostgreSQL has uppercase enum values (PENDING, IN_PROGRESS, COMPLETED) while the application models expect lowercase (pending, in_progress, completed).
3. **Error Handling in Database Fix Scripts**: The scripts fail when encountering already existing backup tables.
4. **Import Error in model_fix.py**: Cannot import 'login' from 'app'.

## Fix Implementation

The fixes are implemented through several scripts:

### 1. `fix_database_compatibility.py`

This is the main script that applies all fixes in the correct order. It:

- Fixes the User model to use the correct table name based on the database dialect
- Fixes PostgreSQL enum values to use lowercase instead of uppercase
- Applies the user_loader fix to handle different table names
- Patches app/__init__.py to automatically apply these fixes on startup

### 2. `model_fix.py`

This script modifies the User model to use the correct table name at runtime:

- For PostgreSQL: Uses 'users' table name
- For SQLite: Uses 'user' table name

It also fixes the login_manager user_loader to handle the different table names.

### 3. `fix_postgresql_enums.py`

This script fixes the enum values in PostgreSQL databases:

- Converts uppercase enum values (PENDING, IN_PROGRESS, COMPLETED) to lowercase (pending, in_progress, completed)
- Handles existing backup tables gracefully
- Provides better error handling for constraint dropping and enum recreation

### 4. `app/user_model_fix.py`

This module provides functions to patch the User model and user_loader at runtime:

- `patch_user_model()`: Updates the User model's __tablename__ attribute based on the database dialect
- `patch_user_loader()`: Patches the Flask-Login user_loader to handle table name differences

### 5. `app_init_patch.py`

This script patches the application's __init__.py file to automatically apply the fixes when the application starts.

## How to Apply the Fixes

### Option 1: Apply All Fixes at Once

Run the main fix script:

```bash
python fix_database_compatibility.py
```

This will:
1. Fix the User model table name
2. Fix PostgreSQL enum values
3. Apply the user_loader fix
4. Patch app/__init__.py to automatically apply these fixes on startup

### Option 2: Apply Individual Fixes

If you prefer to apply fixes individually:

1. Fix the User model table name:
   ```bash
   python model_fix.py
   ```

2. Fix PostgreSQL enum values:
   ```bash
   python fix_postgresql_enums.py
   ```

3. Patch app/__init__.py:
   ```bash
   python app_init_patch.py
   ```

## Automatic Fixes on Application Startup

After applying the fixes, the application will automatically:

1. Detect the database dialect (PostgreSQL or SQLite)
2. Use the correct table name for the User model
3. Handle the user_loader correctly for both database types

This ensures that the application works seamlessly with both PostgreSQL and SQLite databases without manual intervention.

## Reverting the Changes

If you need to revert the changes to app/__init__.py, a backup is created at `app/__init__.py.bak` when you run the fix script. You can restore this backup if needed.

## Troubleshooting

If you encounter issues after applying the fixes:

1. Check the application logs for error messages
2. Verify that the database dialect is correctly detected
3. Ensure that the User model is using the correct table name
4. Check that the enum values in the database match the expected format

If problems persist, you can manually modify the User model in app/models.py to use the correct table name for your database.
