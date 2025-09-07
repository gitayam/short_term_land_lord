"""
Google Cloud Secret Manager integration for secure credential management.
"""

import os
import logging
from typing import Optional

try:
    from google.cloud import secretmanager
    SECRETS_AVAILABLE = True
except ImportError:
    SECRETS_AVAILABLE = False

logger = logging.getLogger(__name__)

class SecretManager:
    """Handle Google Cloud Secret Manager operations."""
    
    def __init__(self):
        self.client = None
        if SECRETS_AVAILABLE:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info("✅ Google Cloud Secret Manager client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize Secret Manager client: {e}")
    
    def get_secret(self, secret_path: str, fallback: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from Google Cloud Secret Manager.
        
        Args:
            secret_path: Full path to secret (e.g., projects/PROJECT/secrets/NAME/versions/latest)
            fallback: Fallback value if secret cannot be retrieved
            
        Returns:
            Secret value or fallback
        """
        if not self.client:
            logger.warning(f"Secret Manager not available, using fallback for {secret_path}")
            return fallback
        
        try:
            response = self.client.access_secret_version(request={"name": secret_path})
            secret_value = response.payload.data.decode("UTF-8")
            logger.info(f"✅ Successfully retrieved secret: {secret_path}")
            return secret_value
        except Exception as e:
            logger.error(f"❌ Failed to retrieve secret {secret_path}: {e}")
            return fallback

# Global instance
secret_manager = SecretManager()

def get_secret_from_env(env_var_name: str, fallback: Optional[str] = None) -> Optional[str]:
    """
    Get a secret using an environment variable that contains the secret path.
    
    Args:
        env_var_name: Environment variable containing the secret path
        fallback: Fallback value if secret cannot be retrieved
        
    Returns:
        Secret value or fallback
    """
    secret_path = os.environ.get(env_var_name)
    if not secret_path:
        logger.warning(f"Environment variable {env_var_name} not set, using fallback")
        return fallback
    
    return secret_manager.get_secret(secret_path, fallback)

def get_app_secrets() -> dict:
    """
    Retrieve all application secrets from Secret Manager.
    
    Returns:
        Dictionary with secret keys and values
    """
    secrets = {}
    
    # Get SECRET_KEY
    secrets['SECRET_KEY'] = get_secret_from_env(
        'SECRET_KEY_PATH', 
        fallback=os.environ.get('SECRET_KEY', 'change-me-in-production')
    )
    
    # Get admin credentials
    secrets['ADMIN_EMAIL'] = get_secret_from_env(
        'ADMIN_EMAIL_PATH',
        fallback=os.environ.get('ADMIN_EMAIL', 'admin@landlord-app.com')
    )
    
    secrets['ADMIN_PASSWORD'] = get_secret_from_env(
        'ADMIN_PASSWORD_PATH',
        fallback=os.environ.get('ADMIN_PASSWORD', 'admin123')
    )
    
    secrets['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'admin')
    
    logger.info(f"✅ Application secrets loaded successfully")
    return secrets