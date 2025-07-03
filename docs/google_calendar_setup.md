# Google Calendar Integration Setup

This guide explains how to set up Google Calendar integration for the property management system.

## Prerequisites

1. A Google Cloud Platform account
2. Access to Google Cloud Console
3. The property management system running locally or on a server

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click on it and press "Enable"

## Step 2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application" as the application type
4. Add authorized redirect URIs:
   - For local development: `http://localhost:5000/profile/google-callback`
   - For production: `https://yourdomain.com/profile/google-callback`
5. Note down the Client ID and Client Secret

## Step 3: Configure Environment Variables

Add the following variables to your `.env` file:

```env
# Google OAuth configuration for Calendar integration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/profile/google-callback
```

For production, update the `GOOGLE_REDIRECT_URI` to your actual domain.

## Step 4: Install Dependencies

Make sure the required Google OAuth packages are installed:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Or update your requirements.txt and run:

```bash
pip install -r requirements.txt
```

## Step 5: Test the Integration

1. Start your application
2. Go to Profile > Connected Services
3. Click "Connect" next to Google Calendar
4. You should be redirected to Google's OAuth consent screen
5. Grant the necessary permissions
6. You should be redirected back to your application with a success message

## Troubleshooting

### Common Issues

1. **"Google Calendar integration is not configured"**
   - Make sure you've set the environment variables correctly
   - Restart your application after adding the variables

2. **"Invalid OAuth state parameter"**
   - This is a security feature. Try the connection process again
   - Make sure your session is working properly

3. **"Failed to access Google Calendar"**
   - Check that the Google Calendar API is enabled in your Google Cloud project
   - Verify that your OAuth consent screen is configured properly

4. **Redirect URI mismatch**
   - Make sure the redirect URI in your Google Cloud Console matches exactly with your `GOOGLE_REDIRECT_URI` environment variable
   - Include the protocol (http/https) and port number if applicable

### Security Considerations

1. **Store credentials securely**: In production, consider encrypting the stored OAuth tokens
2. **Use HTTPS**: Always use HTTPS in production for OAuth flows
3. **Regular token refresh**: Implement token refresh logic for long-term access
4. **Scope limitations**: Only request the minimum necessary scopes

## API Scopes Used

The integration requests the following Google Calendar API scopes:
- `https://www.googleapis.com/auth/calendar.readonly` - Read access to calendars
- `https://www.googleapis.com/auth/calendar.events.readonly` - Read access to calendar events

## Future Enhancements

- Calendar event synchronization
- Two-way sync (create/update events)
- Multiple calendar support
- Calendar sharing between team members
- Automated booking import from Google Calendar 