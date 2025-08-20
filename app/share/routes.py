"""
Routes for shared repair request viewing
"""

from flask import render_template, request, jsonify, flash, redirect, url_for, abort
from flask_login import current_user, login_required
from app import db
from app.share import bp
from app.models import RepairRequest, Task
from app.models import RepairRequestShare, ShareType
from app.services.share_service import ShareService


@bp.route('/repair/<share_token>')
def view_repair_request(share_token):
    """View a shared repair request"""
    share = ShareService.get_share_by_token(share_token)
    
    if not share:
        abort(404, description="Share link not found")
    
    # Check if password is required
    if share.share_type == 'password':
        # Check if password has been verified in session
        import hashlib
        session_key = f"share_auth_{hashlib.md5(share_token.encode()).hexdigest()}"
        from flask import session
        
        if not session.get(session_key):
            return render_template('share/password_prompt.html', 
                                 share_token=share_token)
    
    # Get IP and user agent for logging
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')[:500]  # Limit length
    
    # Verify access
    success, error_message = ShareService.verify_share_access(
        share, None, ip_address, user_agent
    )
    
    if not success:
        flash(error_message, 'danger')
        return render_template('share/error.html', message=error_message), 403
    
    # Get the shared item (repair request or task)
    shared_item = share.shared_item
    if not shared_item:
        abort(404, description="Shared item not found")
    
    # Ensure task_properties are loaded with their related properties
    if hasattr(shared_item, 'task_properties'):
        # Force load the relationship if not already loaded
        _ = shared_item.task_properties
        for tp in shared_item.task_properties:
            _ = tp.property  # Ensure property is loaded
    
    # Render the shared view
    return render_template('share/view_repair_request.html',
                         repair_request=shared_item,
                         share=share)


@bp.route('/repair/<share_token>/verify', methods=['POST'])
def verify_password(share_token):
    """Verify password for protected share"""
    share = ShareService.get_share_by_token(share_token)
    
    if not share:
        abort(404, description="Share link not found")
    
    password = request.form.get('password')
    
    # Get IP and user agent for logging
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')[:500]
    
    # Verify access with password
    success, error_message = ShareService.verify_share_access(
        share, password, ip_address, user_agent
    )
    
    if success:
        # Store in session that password was verified
        import hashlib
        from flask import session
        session_key = f"share_auth_{hashlib.md5(share_token.encode()).hexdigest()}"
        session[session_key] = True
        
        return redirect(url_for('share.view_repair_request', 
                              share_token=share_token))
    else:
        flash(error_message or "Invalid password", 'danger')
        return render_template('share/password_prompt.html',
                             share_token=share_token,
                             error=error_message)


@bp.route('/api/repair/<int:repair_id>/share', methods=['POST'])
@login_required
def create_share(repair_id):
    """Create a new share link for a repair request or repair task"""
    # First try to find it as a Task (repair requests are stored as tasks with tags)
    task = Task.query.get(repair_id)
    if task and task.tags and 'repair_request' in task.tags:
        # This is a task that represents a repair request
        
        # Check permission via task properties
        has_permission = False
        if current_user.is_property_owner:
            # Check if user owns any property associated with this task
            for task_property in task.task_properties:
                if task_property.property.owner_id == current_user.id:
                    has_permission = True
                    break
        elif task.creator_id == current_user.id:
            has_permission = True
        
        if not has_permission:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Use the task as the repair request context
        repair_context = task
    else:
        # Try to find it as a traditional RepairRequest
        repair_request = RepairRequest.query.get_or_404(repair_id)
        
        # Check permission (user must be property owner)
        if repair_request.property.owner_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        repair_context = repair_request
    
    # Get parameters from request
    data = request.get_json()
    
    expires_in_hours = None
    expiration_option = data.get('expiration', 'never')
    if expiration_option == '24h':
        expires_in_hours = 24
    elif expiration_option == '7d':
        expires_in_hours = 24 * 7
    elif expiration_option == '30d':
        expires_in_hours = 24 * 30
    
    password = data.get('password')
    notes = data.get('notes')
    
    # Create the share
    try:
        if isinstance(repair_context, Task):
            # This is a task representing a repair request
            share = ShareService.create_share(
                task_id=repair_id,
                created_by=current_user.id,
                expires_in_hours=expires_in_hours,
                password=password,
                notes=notes
            )
        else:
            # This is a traditional repair request
            share = ShareService.create_share(
                repair_request_id=repair_id,
                created_by=current_user.id,
                expires_in_hours=expires_in_hours,
                password=password,
                notes=notes
            )
        
        return jsonify({
            'success': True,
            'share': share.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/repair/<int:repair_id>/shares', methods=['GET'])
@login_required  
def list_shares(repair_id):
    """List all shares for a repair request"""
    # Get the repair request
    repair_request = RepairRequest.query.get_or_404(repair_id)
    
    # Check permission
    if repair_request.property.owner_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get shares
    shares = ShareService.get_shares_for_request(repair_id)
    
    return jsonify({
        'shares': [share.to_dict() for share in shares]
    })


@bp.route('/api/share/<share_token>', methods=['DELETE'])
@login_required
def revoke_share(share_token):
    """Revoke a share link"""
    share = ShareService.get_share_by_token(share_token)
    
    if not share:
        return jsonify({'error': 'Share not found'}), 404
    
    # Check permission
    if share.created_by != current_user.id:
        # Also check if user owns the property
        repair_request = RepairRequest.query.get(share.repair_request_id)
        if repair_request.property.owner_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
    
    # Revoke the share
    share.revoke()
    
    return jsonify({'success': True, 'message': 'Share link revoked'})


@bp.route('/api/share/<share_token>/stats', methods=['GET'])
@login_required
def share_stats(share_token):
    """Get statistics for a share link"""
    share = ShareService.get_share_by_token(share_token)
    
    if not share:
        return jsonify({'error': 'Share not found'}), 404
    
    # Check permission
    if share.created_by != current_user.id:
        repair_request = RepairRequest.query.get(share.repair_request_id)
        if repair_request.property.owner_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
    
    # Get access logs
    recent_logs = share.access_logs.order_by(
        ShareAccessLog.accessed_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'share': share.to_dict(),
        'recent_access': [{
            'accessed_at': log.accessed_at.isoformat(),
            'ip_address': log.ip_address,
            'access_granted': log.access_granted,
            'failure_reason': log.failure_reason
        } for log in recent_logs]
    })