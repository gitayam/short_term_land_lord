# Guest Access API Documentation

This document provides technical API documentation for the guest access system in the Short Term Landlord property management platform.

## Overview

The guest access system allows property guests to create accounts, browse properties, and manage their booking history through invitation codes. The system provides both public (unauthenticated) and authenticated endpoints.

## Base URL

```
http://localhost:5002
```

## Authentication

The guest system uses two types of authentication:

1. **Invitation Code Authentication**: For initial registration
2. **Session Authentication**: For authenticated guest actions (after login)

## Public Endpoints (No Authentication Required)

### Browse Properties

**GET** `/guest/browse`

Browse available properties without authentication.

**Query Parameters:**
- `city` (string, optional): Filter by city name
- `state` (string, optional): Filter by state code (e.g., "CA", "NY")
- `property_type` (string, optional): Filter by property type ("house", "apartment", "condo", "studio", "suite", "other")
- `min_bedrooms` (integer, optional): Minimum number of bedrooms

**Response:**
```json
{
  "properties": [
    {
      "id": 1,
      "name": "Demo Beach House",
      "city": "Santa Monica",
      "state": "CA",
      "property_type": "house",
      "bedrooms": 3,
      "bathrooms": 2,
      "description": "Beautiful beachfront property with ocean views",
      "amenities": ["WiFi", "Kitchen", "Parking"],
      "images": []
    }
  ],
  "total": 1,
  "filters_applied": {
    "city": null,
    "state": null,
    "property_type": null,
    "min_bedrooms": null
  }
}
```

### Property Details (Public)

**GET** `/guest/browse/property/<int:property_id>`

Get public details for a specific property.

**Response:**
```json
{
  "id": 1,
  "name": "Demo Beach House",
  "city": "Santa Monica",
  "state": "CA",
  "property_type": "house",
  "bedrooms": 3,
  "bathrooms": 2,
  "description": "Beautiful beachfront property with ocean views",
  "amenities": ["WiFi", "Kitchen", "Parking"],
  "images": [],
  "available_for_booking": true
}
```

### Properties API (JSON)

**GET** `/guest/api/properties`

JSON API endpoint for property listings.

**Query Parameters:** Same as `/guest/browse`

**Response:** JSON array of properties (same structure as browse endpoint)

### Check Invitation Status

**GET** `/guest/api/invitation/<code>/status`

Check if an invitation code is valid and available.

**Path Parameters:**
- `code` (string): The invitation code to check

**Response:**
```json
{
  "valid": true,
  "available": true,
  "expired": false,
  "property_name": "Demo Beach House",
  "expires_at": "2025-09-15T12:00:00Z"
}
```

**Error Response:**
```json
{
  "valid": false,
  "available": false,
  "expired": false,
  "error": "Invitation code not found"
}
```

## Guest Registration

### Registration with Invitation Code

**GET** `/guest/register/<code>`

Display registration form for a specific invitation code.

**POST** `/guest/register/<code>`

Submit guest registration form.

**Request Body:**
```json
{
  "invitation_code": "ABC123XYZ",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "phone": "+1234567890",
  "marketing_emails_consent": false,
  "booking_reminders_consent": true
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Account created successfully! Please check your email to verify your account.",
  "user_id": 123,
  "redirect_url": "/auth/login"
}
```

**Error Response:**
```json
{
  "success": false,
  "errors": {
    "invitation_code": ["Invalid invitation code."],
    "email": ["An account with this email already exists."]
  }
}
```

### Registration Help

**GET** `/guest/register/help`

Display help page for guests who need invitation codes.

## Authenticated Guest Endpoints

### Guest Dashboard

**GET** `/guest/dashboard`

**Authentication Required:** Guest user session

Display guest dashboard with booking history and account information.

**Response:** HTML page with:
- Current and upcoming bookings
- Past booking history
- Account profile information
- Quick actions (update profile, book again, etc.)

### Guest Profile Management

**GET** `/guest/profile`

Display guest profile edit form.

**POST** `/guest/profile`

Update guest profile information.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "timezone": "US/Pacific",
  "language": "en",
  "theme_preference": "light",
  "marketing_emails_consent": true,
  "booking_reminders_consent": true,
  "email_notifications": true
}
```

### Booking History

**GET** `/guest/bookings`

**Authentication Required:** Guest user session

Get guest's booking history.

**Response:**
```json
{
  "bookings": [
    {
      "id": 1,
      "property_name": "Demo Beach House",
      "property_id": 1,
      "check_in_date": "2025-08-01",
      "check_out_date": "2025-08-07",
      "booking_source": "airbnb",
      "external_booking_id": "HMABCD123456",
      "status": "completed",
      "nights": 6,
      "created_at": "2025-07-15T10:30:00Z"
    }
  ],
  "total": 1,
  "upcoming_count": 0,
  "past_count": 1
}
```

### Direct Booking (Future Feature)

**POST** `/guest/book/<int:property_id>`

**Authentication Required:** Guest user session

Create a direct booking for a property.

**Request Body:**
```json
{
  "check_in_date": "2025-09-01",
  "check_out_date": "2025-09-07",
  "guest_count": 2,
  "special_requests": "Late check-in requested"
}
```

## Admin Endpoints (Guest Management)

### List Guest Invitations

**GET** `/guest/admin/invitations`

**Authentication Required:** Admin user session

Display all guest invitations with management options.

### Create Guest Invitation

**GET** `/guest/admin/invitations/create`

Display invitation creation form.

**POST** `/guest/admin/invitations/create`

Create new guest invitation.

**Request Body:**
```json
{
  "property_id": 1,
  "email": "guest@example.com",
  "guest_name": "Jane Smith",
  "expires_in_days": 30,
  "max_uses": 1,
  "notes": "VIP guest for September booking"
}
```

### Manage Specific Invitation

**GET** `/guest/admin/invitations/<int:invitation_id>`

Display invitation details and management options.

**POST** `/guest/admin/invitations/<int:invitation_id>/extend`

Extend invitation expiration date.

**POST** `/guest/admin/invitations/<int:invitation_id>/deactivate`

Deactivate an invitation.

### Bulk Invitation Creation

**POST** `/guest/admin/invitations/bulk`

Create multiple invitations at once.

**Request Body:**
```json
{
  "property_id": 1,
  "guest_emails": "guest1@example.com\nguest2@example.com\nguest3@example.com",
  "expires_in_days": 30,
  "notes": "Bulk invitations for summer guests"
}
```

## Error Codes

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., email already exists)
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### Custom Error Codes

- `INVALID_INVITATION_CODE`: Invitation code does not exist
- `EXPIRED_INVITATION_CODE`: Invitation code has expired
- `USED_INVITATION_CODE`: Invitation code already used
- `EMAIL_ALREADY_EXISTS`: Email address already registered
- `PROPERTY_NOT_AVAILABLE`: Property not available for guest access

## Rate Limiting

- **Public endpoints**: 100 requests per minute per IP
- **Registration endpoints**: 10 requests per minute per IP
- **Authenticated endpoints**: 200 requests per minute per user

## Data Models

### GuestInvitation

```json
{
  "id": 1,
  "code": "ABC123XYZ789",
  "property_id": 1,
  "property_name": "Demo Beach House",
  "created_by_id": 1,
  "created_by_name": "Admin User",
  "email": "guest@example.com",
  "guest_name": "John Doe",
  "expires_at": "2025-09-15T12:00:00Z",
  "used_at": null,
  "used_by_id": null,
  "is_active": true,
  "max_uses": 1,
  "current_uses": 0,
  "notes": "VIP guest invitation",
  "created_at": "2025-08-15T12:00:00Z"
}
```

### GuestBooking

```json
{
  "id": 1,
  "guest_user_id": 123,
  "property_id": 1,
  "property_name": "Demo Beach House",
  "check_in_date": "2025-08-01",
  "check_out_date": "2025-08-07",
  "booking_source": "airbnb",
  "external_booking_id": "HMABCD123456",
  "status": "confirmed",
  "guest_count": 2,
  "special_requests": "Late check-in",
  "created_at": "2025-07-15T10:30:00Z"
}
```

### Guest User Profile

```json
{
  "id": 123,
  "email": "guest@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "role": "property_guest",
  "is_active": true,
  "email_verified": true,
  "last_login": "2025-08-15T14:30:00Z",
  "created_at": "2025-08-01T12:00:00Z",
  "preferences": {
    "timezone": "US/Pacific",
    "language": "en",
    "theme": "light",
    "marketing_emails": false,
    "booking_reminders": true,
    "email_notifications": true
  }
}
```

## Security Considerations

- All invitation codes are generated using cryptographically secure random functions
- Invitation codes avoid similar-looking characters (0, O, l, I) to prevent confusion
- Email verification is required for all guest accounts
- Rate limiting prevents abuse of registration endpoints
- Guest users have restricted access compared to admin users
- All sensitive endpoints require proper authentication
- Input validation prevents injection attacks

## Testing

### Test Data

Use the demo script to create test data:

```bash
python3 demo_guest_system.py
```

This creates:
- Admin user: `admin@demo.com` (password: `admin123`)
- Demo property: "Demo Beach House"
- Sample invitation code (8 characters)

### Example API Calls

```bash
# Check invitation status
curl "http://localhost:5002/guest/api/invitation/ABC123XYZ/status"

# Browse properties
curl "http://localhost:5002/guest/api/properties?city=Santa Monica&property_type=house"

# Get property details
curl "http://localhost:5002/guest/browse/property/1"
```

## Changelog

### Version 1.0 (August 2025)
- Initial guest access system implementation
- Flexible invitation codes (5-24 characters)
- Public property browsing
- Guest registration and authentication
- Admin invitation management
- API endpoints for integration