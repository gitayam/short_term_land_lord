"""
Service for managing repair request shares
"""

import secrets
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import RepairRequestShare, ShareAccessLog, ShareType


class ShareService:
    """Service for creating and managing repair request shares"""
    
    @staticmethod
    def generate_token(length=32):
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @classmethod
    def create_share(cls, repair_request_id=None, task_id=None, created_by=None, expires_in_hours=None, 
                    password=None, notes=None):
        """
        Create a new share link for a repair request or task
        
        Args:
            repair_request_id: ID of the repair request to share (optional)
            task_id: ID of the task to share (optional)
            created_by: User ID who created the share
            expires_in_hours: Hours until expiration (None for no expiration)
            password: Optional password for protection
            notes: Optional notes about the share
        
        Returns:
            RepairRequestShare instance
        """
        if not repair_request_id and not task_id:
            raise ValueError("Either repair_request_id or task_id must be provided")
        
        share = RepairRequestShare(
            repair_request_id=repair_request_id,
            task_id=task_id,
            share_token=cls.generate_token(),
            created_by=created_by,
            notes=notes
        )
        
        # Set expiration if specified
        if expires_in_hours:
            share.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Set password if provided
        if password:
            share.set_password(password)
        
        db.session.add(share)
        db.session.commit()
        
        return share
    
    @staticmethod
    def get_share_by_token(token):
        """Get a share by its token"""
        return RepairRequestShare.query.filter_by(
            share_token=token
        ).first()
    
    @staticmethod
    def get_active_share_by_token(token):
        """Get an active (valid) share by its token"""
        share = RepairRequestShare.query.filter_by(
            share_token=token,
            is_active=True
        ).first()
        
        if share and share.is_valid():
            return share
        return None
    
    @staticmethod
    def verify_share_access(share, password=None, ip_address=None, user_agent=None):
        """
        Verify access to a shared link
        
        Args:
            share: RepairRequestShare instance
            password: Password attempt (if required)
            ip_address: IP address of requester
            user_agent: User agent string
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        # Check if share is active
        if not share.is_active:
            ShareAccessLog.log_access(
                share.id, ip_address, user_agent, 
                access_granted=False, 
                failure_reason='Share link is inactive'
            )
            return False, "This share link has been revoked"
        
        # Check if share is expired
        if share.is_expired():
            ShareAccessLog.log_access(
                share.id, ip_address, user_agent,
                access_granted=False,
                failure_reason='Share link is expired'
            )
            return False, "This share link has expired"
        
        # Check password if required
        if share.share_type == 'password':
            if not password or not share.check_password(password):
                ShareAccessLog.log_access(
                    share.id, ip_address, user_agent,
                    access_granted=False,
                    failure_reason='Invalid password'
                )
                return False, "Invalid password"
        
        # Access granted
        ShareAccessLog.log_access(
            share.id, ip_address, user_agent,
            access_granted=True
        )
        share.increment_view_count()
        
        return True, None
    
    @staticmethod
    def get_shares_for_request(repair_request_id, active_only=True):
        """Get all shares for a repair request"""
        query = RepairRequestShare.query.filter_by(
            repair_request_id=repair_request_id
        )
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(RepairRequestShare.created_at.desc()).all()
    
    @staticmethod
    def get_shares_by_user(user_id, active_only=True):
        """Get all shares created by a user"""
        query = RepairRequestShare.query.filter_by(
            created_by=user_id
        )
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(RepairRequestShare.created_at.desc()).all()
    
    @staticmethod
    def revoke_share(share_id, user_id=None):
        """
        Revoke a share link
        
        Args:
            share_id: ID of the share to revoke
            user_id: Optional user ID to verify ownership
        
        Returns:
            bool: Success status
        """
        share = RepairRequestShare.query.get(share_id)
        
        if not share:
            return False
        
        # Verify ownership if user_id provided
        if user_id and share.created_by != user_id:
            return False
        
        share.revoke()
        return True
    
    @staticmethod
    def cleanup_expired_shares():
        """Clean up expired shares (can be run as a scheduled job)"""
        expired_shares = RepairRequestShare.query.filter(
            RepairRequestShare.expires_at < datetime.utcnow(),
            RepairRequestShare.is_active == True
        ).all()
        
        for share in expired_shares:
            share.is_active = False
        
        db.session.commit()
        return len(expired_shares)