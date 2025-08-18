"""
Tests for the configuration management system
"""

import unittest
import os
from app import create_app, db
from app.models import User, SiteSetting, ConfigurationAudit
from app.utils.configuration import config_service, ConfigurationCategory, ConfigurationType
from config import TestConfig


class ConfigurationTestCase(unittest.TestCase):
    """Test cases for configuration management"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Create database tables
        db.create_all()
        
        # Create test admin user
        self.admin_user = User(
            email='admin@test.com',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_admin=True
        )
        self.admin_user.set_password('testpass123')
        db.session.add(self.admin_user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_configuration_hierarchy(self):
        """Test the three-tier configuration hierarchy"""
        # Test 1: Environment variable takes precedence
        os.environ['TEST_CONFIG_KEY'] = 'env_value'
        value = config_service.get('TEST_CONFIG_KEY', 'default_value')
        self.assertEqual(value, 'env_value')
        
        # Clean up environment variable
        del os.environ['TEST_CONFIG_KEY']
        
        # Test 2: Database value is used when no env var
        SiteSetting.set_setting('APP_NAME', 'Database App Name')
        value = config_service.get('APP_NAME')
        self.assertEqual(value, 'Database App Name')
        
        # Test 3: Default value from registry
        value = config_service.get('MAX_PROPERTIES_PER_USER')
        self.assertEqual(value, 10)  # Default from registry
        
        # Test 4: Provided default when nothing else available
        value = config_service.get('NON_EXISTENT_KEY', 'my_default')
        self.assertEqual(value, 'my_default')
    
    def test_configuration_types(self):
        """Test type conversion for different configuration types"""
        # Test boolean conversion
        os.environ['TEST_BOOL'] = 'true'
        self.assertTrue(config_service._convert_value('true', ConfigurationType.BOOLEAN))
        self.assertFalse(config_service._convert_value('false', ConfigurationType.BOOLEAN))
        
        # Test integer conversion
        self.assertEqual(config_service._convert_value('42', ConfigurationType.INTEGER), 42)
        
        # Test float conversion
        self.assertEqual(config_service._convert_value('3.14', ConfigurationType.FLOAT), 3.14)
        
        # Clean up
        del os.environ['TEST_BOOL']
    
    def test_configuration_validation(self):
        """Test configuration validation rules"""
        # Get a config item with validation rules
        all_settings = config_service.get_all_by_category()
        max_props_setting = all_settings.get('MAX_PROPERTIES_PER_USER')
        
        # Test that validation rules are present
        self.assertIsNotNone(max_props_setting['validation'])
        self.assertEqual(max_props_setting['validation']['min'], 1)
        self.assertEqual(max_props_setting['validation']['max'], 100)
        
        # Test setting with invalid value (should fail)
        success = config_service.set('MAX_PROPERTIES_PER_USER', 200, self.admin_user.id)
        self.assertFalse(success)
        
        # Test setting with valid value (should succeed)
        success = config_service.set('MAX_PROPERTIES_PER_USER', 50, self.admin_user.id)
        self.assertTrue(success)
    
    def test_sensitive_configuration(self):
        """Test that sensitive configurations are handled properly"""
        # Get all settings
        all_settings = config_service.get_all_by_category()
        
        # Check that SECRET_KEY is marked as sensitive
        secret_key_setting = all_settings.get('SECRET_KEY')
        if secret_key_setting:
            self.assertTrue(secret_key_setting['sensitive'])
            self.assertFalse(secret_key_setting['editable'])
            
            # Sensitive values should be masked in display
            self.assertEqual(secret_key_setting['display_value'], '********')
    
    def test_configuration_categories(self):
        """Test configuration categorization"""
        categories = config_service.get_categories()
        
        # Check that expected categories exist
        expected_categories = [
            ConfigurationCategory.SYSTEM,
            ConfigurationCategory.APPLICATION,
            ConfigurationCategory.FEATURES,
            ConfigurationCategory.EMAIL,
            ConfigurationCategory.SECURITY
        ]
        
        for category in expected_categories:
            self.assertIn(category, categories)
        
        # Test getting settings by category
        app_settings = config_service.get_all_by_category(ConfigurationCategory.APPLICATION)
        self.assertTrue(len(app_settings) > 0)
        
        # Check that all returned settings are in the correct category
        for key, setting in app_settings.items():
            self.assertEqual(setting['category'], ConfigurationCategory.APPLICATION)
    
    def test_configuration_audit(self):
        """Test configuration change audit logging"""
        # Make a configuration change
        config_service.set('APP_NAME', 'New App Name', self.admin_user.id)
        
        # Check that audit log was created
        audit_logs = ConfigurationAudit.query.filter_by(
            setting_key='APP_NAME',
            changed_by_id=self.admin_user.id
        ).all()
        
        self.assertTrue(len(audit_logs) > 0)
        
        # Verify audit log details
        latest_log = audit_logs[-1]
        self.assertEqual(latest_log.new_value, 'New App Name')
        self.assertEqual(latest_log.changed_by_id, self.admin_user.id)
    
    def test_configuration_reset_to_default(self):
        """Test resetting a configuration to its default value"""
        # Set a custom value
        config_service.set('MAX_PROPERTIES_PER_USER', 25, self.admin_user.id)
        self.assertEqual(config_service.get('MAX_PROPERTIES_PER_USER'), 25)
        
        # Reset to default
        all_settings = config_service.get_all_by_category()
        default_value = all_settings['MAX_PROPERTIES_PER_USER']['default']
        config_service.set('MAX_PROPERTIES_PER_USER', default_value, self.admin_user.id)
        
        # Verify it's back to default
        self.assertEqual(config_service.get('MAX_PROPERTIES_PER_USER'), 10)
    
    def test_configuration_caching(self):
        """Test that configuration values are cached properly"""
        # Get a value (should cache it)
        value1 = config_service.get('APP_NAME')
        
        # Get it again (should come from cache)
        value2 = config_service.get('APP_NAME')
        
        self.assertEqual(value1, value2)
        
        # Set a new value (should clear cache)
        config_service.set('APP_NAME', 'Updated Name', self.admin_user.id)
        
        # Get again (should reflect new value)
        value3 = config_service.get('APP_NAME')
        self.assertEqual(value3, 'Updated Name')
    
    def test_boolean_feature_flags(self):
        """Test boolean feature flags work correctly"""
        # Test enabling a feature
        config_service.set('ENABLE_GUEST_REVIEWS', True, self.admin_user.id)
        self.assertTrue(config_service.get('ENABLE_GUEST_REVIEWS'))
        
        # Test disabling a feature
        config_service.set('ENABLE_GUEST_REVIEWS', False, self.admin_user.id)
        self.assertFalse(config_service.get('ENABLE_GUEST_REVIEWS'))
        
        # Test string representation of boolean
        config_service.set('ENABLE_AI_FEATURES', 'true', self.admin_user.id)
        self.assertTrue(config_service.get('ENABLE_AI_FEATURES'))


if __name__ == '__main__':
    unittest.main()