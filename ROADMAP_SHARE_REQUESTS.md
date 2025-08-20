# Repair Request Sharing Feature Roadmap

## Overview
Implement a secure sharing system for repair requests that allows property owners to share specific repair requests with contractors, insurance companies, or other stakeholders via secure links.

## Branch Name
`feature/share-repair-requests`

## Key Features

### 1. Share Link Generation
- Generate unique, cryptographically secure tokens for each share
- Support two sharing modes:
  - **Public**: Accessible to anyone with the link
  - **Password-protected**: Requires additional password to view
- Customizable expiration times (24h, 7d, 30d, never)

### 2. Security Considerations
- **Token Generation**: Use `secrets.token_urlsafe()` for unpredictable tokens
- **Rate Limiting**: Prevent brute force attempts on password-protected shares
- **Data Isolation**: Shared views only expose necessary repair request data
- **No Authentication Leak**: Shared pages don't reveal system login or user data
- **HTTPS Only**: Enforce secure connections for shared links

### 3. Database Schema

```sql
-- New table: repair_request_shares
CREATE TABLE repair_request_shares (
    id SERIAL PRIMARY KEY,
    repair_request_id INTEGER REFERENCES repair_request(id) ON DELETE CASCADE,
    share_token VARCHAR(255) UNIQUE NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP,
    share_type VARCHAR(50) DEFAULT 'public', -- 'public' or 'password'
    notes TEXT -- Optional notes about why/who it's shared with
);

-- New table: share_access_logs
CREATE TABLE share_access_logs (
    id SERIAL PRIMARY KEY,
    share_id INTEGER REFERENCES repair_request_shares(id) ON DELETE CASCADE,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    access_granted BOOLEAN DEFAULT TRUE
);
```

### 4. URL Structure
- Share URL: `/share/repair/{share_token}`
- Password verification: `/share/repair/{share_token}/verify`

### 5. UI Components

#### Share Dialog (Modal)
- Toggle: Public vs Password-protected
- Password field (if protected)
- Expiration selector
- Notes field (optional)
- Copy link button
- QR code generation (optional)

#### Shared View Page
- Clean, focused layout (no navigation bars)
- Repair request details:
  - Title and description
  - Status and priority
  - Property info (limited)
  - Photos/attachments
  - Timeline/updates (if applicable)
- Branding footer
- "Request access" button for contractors

#### Management Interface
- List of active shares
- Revoke/expire shares
- View access logs
- Regenerate links

### 6. Implementation Phases

#### Phase 1: Core Infrastructure (Current)
1. Create database migrations
2. Add share model and relationships
3. Implement token generation service

#### Phase 2: Basic Sharing
1. Create share generation endpoint
2. Build public view template
3. Add share button to repair request UI

#### Phase 3: Security Features
1. Add password protection
2. Implement expiration logic
3. Add rate limiting

#### Phase 4: Advanced Features
1. Access logging and analytics
2. QR code generation
3. Email share notifications
4. Contractor response system

### 7. API Endpoints

```python
# Share management
POST   /api/repair-request/{id}/share       # Create share link
GET    /api/repair-request/{id}/shares      # List all shares
DELETE /api/share/{share_token}             # Revoke share
PATCH  /api/share/{share_token}             # Update share settings

# Public access
GET    /share/repair/{share_token}          # View shared request
POST   /share/repair/{share_token}/verify   # Verify password
```

### 8. Security Best Practices

1. **Token Security**
   - Minimum 32 bytes of entropy
   - URL-safe base64 encoding
   - Store hashed in database (optional)

2. **Password Protection**
   - Bcrypt for password hashing
   - Minimum password requirements
   - Failed attempt tracking

3. **Access Control**
   - Check expiration on every access
   - Verify share is still active
   - Log all access attempts

4. **Data Privacy**
   - Don't expose user emails/phones
   - Limit property information
   - No system internals

### 9. Testing Strategy

- Unit tests for token generation
- Integration tests for share creation/access
- Security tests for password protection
- Performance tests for high-traffic shares
- E2E tests for complete share workflow

### 10. Future Enhancements

- Contractor portal for responding to shared requests
- Integration with messaging system
- Analytics dashboard for share performance
- Bulk sharing for multiple requests
- Template system for common share scenarios
- WebSocket for real-time updates on shared pages

## Success Metrics

- Time to share creation < 2 seconds
- Share page load time < 1 second
- Zero security vulnerabilities
- 90% of shares accessed successfully
- User satisfaction score > 4.5/5

## Timeline

- Week 1: Database and core models
- Week 2: Basic sharing functionality
- Week 3: Security features and password protection
- Week 4: UI polish and testing