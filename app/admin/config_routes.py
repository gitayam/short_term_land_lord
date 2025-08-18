from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import SiteSetting, ConfigurationAudit
from app.auth.decorators import admin_required
from app.utils.configuration import config_service, ConfigurationCategory, ConfigurationType
import json

bp = Blueprint('admin_config', __name__, url_prefix='/admin/configuration')


@bp.route('/')
@login_required
@admin_required
def index():
    """Main configuration page showing all categories"""
    categories = config_service.get_categories()
    category_info = {
        ConfigurationCategory.SYSTEM: {
            'icon': 'fas fa-server',
            'description': 'Core system settings (mostly read-only)',
            'color': 'danger'
        },
        ConfigurationCategory.APPLICATION: {
            'icon': 'fas fa-cogs',
            'description': 'General application settings',
            'color': 'primary'
        },
        ConfigurationCategory.FEATURES: {
            'icon': 'fas fa-toggle-on',
            'description': 'Feature flags and toggles',
            'color': 'success'
        },
        ConfigurationCategory.EMAIL: {
            'icon': 'fas fa-envelope',
            'description': 'Email server and notification settings',
            'color': 'info'
        },
        ConfigurationCategory.SMS: {
            'icon': 'fas fa-sms',
            'description': 'SMS and Twilio configuration',
            'color': 'warning'
        },
        ConfigurationCategory.STORAGE: {
            'icon': 'fas fa-database',
            'description': 'File storage and upload settings',
            'color': 'secondary'
        },
        ConfigurationCategory.SECURITY: {
            'icon': 'fas fa-shield-alt',
            'description': 'Security and authentication settings',
            'color': 'danger'
        },
        ConfigurationCategory.INTEGRATION: {
            'icon': 'fas fa-plug',
            'description': 'Third-party service integrations',
            'color': 'dark'
        },
        ConfigurationCategory.PERFORMANCE: {
            'icon': 'fas fa-tachometer-alt',
            'description': 'Performance and optimization settings',
            'color': 'light'
        }
    }
    
    # Get count of editable settings per category
    all_settings = config_service.get_all_by_category()
    category_counts = {}
    for category in categories:
        category_settings = [s for k, s in all_settings.items() if s['category'] == category]
        editable_count = sum(1 for s in category_settings if s['editable'])
        total_count = len(category_settings)
        category_counts[category] = {'editable': editable_count, 'total': total_count}
    
    return render_template('admin/configuration/index.html',
                          categories=categories,
                          category_info=category_info,
                          category_counts=category_counts,
                          title='Configuration Management')


@bp.route('/category/<category>')
@login_required
@admin_required
def category_settings(category):
    """View and edit settings for a specific category"""
    # Get all settings for this category
    all_settings = config_service.get_all_by_category(category)
    
    if not all_settings:
        flash(f'No settings found for category: {category}', 'warning')
        return redirect(url_for('admin_config.index'))
    
    # Separate editable and read-only settings
    editable_settings = {k: v for k, v in all_settings.items() if v['editable']}
    readonly_settings = {k: v for k, v in all_settings.items() if not v['editable']}
    
    # Get category info
    category_info = {
        ConfigurationCategory.SYSTEM: {'name': 'System Settings', 'icon': 'fas fa-server'},
        ConfigurationCategory.APPLICATION: {'name': 'Application Settings', 'icon': 'fas fa-cogs'},
        ConfigurationCategory.FEATURES: {'name': 'Feature Flags', 'icon': 'fas fa-toggle-on'},
        ConfigurationCategory.EMAIL: {'name': 'Email Configuration', 'icon': 'fas fa-envelope'},
        ConfigurationCategory.SMS: {'name': 'SMS Configuration', 'icon': 'fas fa-sms'},
        ConfigurationCategory.STORAGE: {'name': 'Storage Settings', 'icon': 'fas fa-database'},
        ConfigurationCategory.SECURITY: {'name': 'Security Settings', 'icon': 'fas fa-shield-alt'},
        ConfigurationCategory.INTEGRATION: {'name': 'Integration Settings', 'icon': 'fas fa-plug'},
        ConfigurationCategory.PERFORMANCE: {'name': 'Performance Settings', 'icon': 'fas fa-tachometer-alt'}
    }.get(category, {'name': category, 'icon': 'fas fa-cog'})
    
    return render_template('admin/configuration/category.html',
                          category=category,
                          category_info=category_info,
                          editable_settings=editable_settings,
                          readonly_settings=readonly_settings,
                          ConfigurationType=ConfigurationType,
                          title=category_info['name'])


@bp.route('/update', methods=['POST'])
@login_required
@admin_required
def update_setting():
    """Update a configuration setting via AJAX"""
    try:
        data = request.get_json()
        key = data.get('key')
        value = data.get('value')
        
        if not key:
            return jsonify({'success': False, 'error': 'Setting key is required'}), 400
        
        # Special handling for boolean values
        if isinstance(value, str) and value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        
        # Update the setting
        success = config_service.set(key, value, current_user.id)
        
        if success:
            # Get the updated setting info
            all_settings = config_service.get_all_by_category()
            updated_setting = all_settings.get(key, {})
            
            return jsonify({
                'success': True,
                'message': f'Setting "{key}" updated successfully',
                'setting': {
                    'key': key,
                    'value': updated_setting.get('value'),
                    'display_value': updated_setting.get('display_value')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to update setting "{key}". Check validation rules.'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error updating setting: {str(e)}'
        }), 500


@bp.route('/batch-update', methods=['POST'])
@login_required
@admin_required
def batch_update():
    """Update multiple settings at once"""
    try:
        settings = request.get_json()
        
        if not settings or not isinstance(settings, dict):
            return jsonify({'success': False, 'error': 'Invalid settings data'}), 400
        
        results = []
        errors = []
        
        for key, value in settings.items():
            # Special handling for boolean values
            if isinstance(value, str) and value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            
            success = config_service.set(key, value, current_user.id)
            if success:
                results.append(key)
            else:
                errors.append(f'Failed to update "{key}"')
        
        if errors:
            return jsonify({
                'success': False,
                'message': f'Updated {len(results)} settings with {len(errors)} errors',
                'updated': results,
                'errors': errors
            }), 207  # Multi-Status
        else:
            return jsonify({
                'success': True,
                'message': f'Successfully updated {len(results)} settings',
                'updated': results
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error updating settings: {str(e)}'
        }), 500


@bp.route('/audit')
@login_required
@admin_required
def audit_log():
    """View configuration change audit log"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Get audit logs with pagination
    audit_logs = ConfigurationAudit.query\
        .order_by(ConfigurationAudit.changed_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/configuration/audit.html',
                          audit_logs=audit_logs,
                          title='Configuration Audit Log')


@bp.route('/export')
@login_required
@admin_required
def export_config():
    """Export current configuration as JSON"""
    all_settings = config_service.get_all_by_category()
    
    # Remove sensitive values from export
    export_data = {}
    for key, setting in all_settings.items():
        if not setting['sensitive']:
            export_data[key] = {
                'value': setting['value'],
                'category': setting['category'],
                'type': setting['type'],
                'description': setting['description']
            }
    
    response = jsonify(export_data)
    response.headers['Content-Disposition'] = 'attachment; filename=config_export.json'
    return response


@bp.route('/reset/<key>', methods=['POST'])
@login_required
@admin_required
def reset_setting(key):
    """Reset a setting to its default value"""
    try:
        # Get the default value from registry
        all_settings = config_service.get_all_by_category()
        setting_info = all_settings.get(key)
        
        if not setting_info:
            return jsonify({'success': False, 'error': 'Setting not found'}), 404
        
        if not setting_info['editable']:
            return jsonify({'success': False, 'error': 'This setting cannot be modified'}), 403
        
        default_value = setting_info.get('default')
        if default_value is not None:
            success = config_service.set(key, default_value, current_user.id)
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Setting "{key}" reset to default',
                    'default_value': default_value
                })
        
        return jsonify({
            'success': False,
            'error': 'No default value available for this setting'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error resetting setting: {str(e)}'
        }), 500