# Admin Access Guide

## Quick Access to Admin Features

### For Admin Users

When logged in as an admin user, you now have quick access to administrative features directly from the navigation bar dropdown menu.

#### Navigation Bar Dropdown
Click on your name in the top-right corner to see:

```
[Your Name] ▼
├── 👤 My Profile
├── ─────────────────
├── Administration
├── 🎯 Admin Dashboard
├── 🎛️ Configuration
├── ⚙️ Site Settings
├── 👥 User Management
├── ─────────────────
└── 🚪 Logout
```

### Direct URLs

#### Configuration Management
- **Main Page**: http://localhost:5001/admin/configuration/
- **Category View**: http://localhost:5001/admin/configuration/category/[category_name]
- **Audit Log**: http://localhost:5001/admin/configuration/audit
- **Export Config**: http://localhost:5001/admin/configuration/export

#### Admin Dashboard
- **Dashboard**: http://localhost:5001/admin/dashboard
- **Settings**: http://localhost:5001/admin/settings
- **Users**: http://localhost:5001/admin/users
- **Registrations**: http://localhost:5001/admin/registrations

## Admin User Accounts

These accounts have admin privileges:
- `admin@landlord.com`
- `admin@demo.com`
- `issac@alfaren.xyz`

## Configuration Management Features

### Three-Tier Configuration Hierarchy
1. **Environment Variables** (.env file) - Highest priority
2. **Database Settings** - Editable via admin UI
3. **Default Values** - Built-in fallbacks

### Configuration Categories

| Category | Description | Editable Items |
|----------|-------------|----------------|
| **System** | Core system settings | Read-only |
| **Application** | General app settings | App name, limits, timezone |
| **Features** | Feature flags | Guest reviews, AI, SMS, Analytics |
| **Email** | SMTP configuration | Server, port, sender |
| **SMS** | Twilio settings | Phone number (credentials are env-only) |
| **Storage** | File uploads | Backend type, max size |
| **Security** | Auth settings | Session lifetime, password rules |
| **Integration** | Third-party APIs | API keys (env-only) |
| **Performance** | Optimization | Cache timeout, pool size |

### Key Features
- ✅ Live editing of non-sensitive settings
- ✅ Audit logging with user tracking
- ✅ Export configuration as JSON
- ✅ Reset to defaults
- ✅ Sensitive value protection
- ✅ Type validation
- ✅ Category-based organization

## How It Works

### Setting Priority
```
1. Check environment variable
   ↓ (if not found)
2. Check database setting
   ↓ (if not found)
3. Use default from registry
   ↓ (if not defined)
4. Use provided fallback
```

### Security Features
- Sensitive settings (passwords, API keys) can only be set via environment variables
- All configuration changes are logged with user attribution
- CSRF protection on all configuration endpoints
- Admin role required for access

## Troubleshooting

### Can't see admin menu?
- Ensure you're logged in with an admin account
- Check that `current_user.is_admin` is True

### Configuration page not loading?
- Clear browser cache
- Restart Flask application
- Check that migrations have been run

### Settings not saving?
- Check validation rules (min/max values)
- Ensure setting is marked as editable
- Check browser console for errors

## Technical Details

### Files Modified
- `app/templates/base.html` - Added admin dropdown menu
- `app/admin/routes.py` - Fixed blueprint import
- `app/admin/config_routes.py` - Configuration management routes
- `app/utils/configuration.py` - Configuration service
- `app/models.py` - Extended SiteSetting model

### Database Changes
- Added columns to `site_settings` table:
  - `category` - Setting category
  - `config_type` - Data type
  - `updated_by_id` - User who made change
- Created `configuration_audit` table for change tracking

---

*Configuration Management System v1.4.0*