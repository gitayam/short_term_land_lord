# Short Term Landlord - Google App Engine Deployment Guide

## Overview

This guide walks you through deploying the Short Term Landlord Flask application to Google App Engine. The application provides property management features including interactive guidebooks for guests and worker calendar access.

## Prerequisites

### 1. Google Cloud Account
- Active Google Cloud account with billing enabled
- Google Cloud CLI (`gcloud`) installed and configured
- Project with App Engine enabled

### 2. Local Setup
```bash
# Clone the repository
git clone <your-repository-url>
cd short_term_land_lord

# Install Google Cloud CLI (if not already installed)
# macOS: brew install google-cloud-sdk
# Linux: Follow https://cloud.google.com/sdk/docs/install

# Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login
```

### 3. Required APIs
The deployment script will automatically enable these APIs:
- App Engine Admin API
- Cloud Build API
- Cloud SQL Admin API
- Secret Manager API
- Cloud Logging API
- Cloud Monitoring API

## Quick Deployment

### Option 1: Automated Script (Recommended)
```bash
# Run the deployment script
./deploy.sh --project-id your-project-id --region us-central1

# Or with environment variables
export GOOGLE_CLOUD_PROJECT_ID="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"
./deploy.sh
```

### Option 2: Manual Deployment
```bash
# 1. Set up project
gcloud config set project your-project-id
gcloud app create --region=us-central1

# 2. Enable APIs
gcloud services enable appengine.googleapis.com cloudsql.googleapis.com secretmanager.googleapis.com

# 3. Deploy
gcloud app deploy app.yaml
```

## Configuration

### 1. Update app.yaml
Edit `app.yaml` to configure your environment variables:

```yaml
env_variables:
  FLASK_ENV: production
  SECRET_KEY: "your-secret-key-here"
  DATABASE_URL: "postgresql://user:password@/cloudsql/project:region:instance/database"
  GOOGLE_CLOUD_PROJECT_ID: "your-project-id"
  # ... other variables
```

### 2. Database Setup

#### Option A: Cloud SQL (Recommended)
```bash
# Create Cloud SQL instance
gcloud sql instances create landlord-postgres \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1

# Create database
gcloud sql databases create landlord_db --instance=landlord-postgres

# Create user
gcloud sql users create app_user --instance=landlord-postgres --password=secure_password

# Get connection string
gcloud sql instances describe landlord-postgres --format="value(connectionName)"
```

#### Option B: External Database
Update the `DATABASE_URL` in `app.yaml` with your external PostgreSQL connection string.

### 3. Redis Setup (Optional)
For caching and sessions:

```bash
# Create Redis instance
gcloud redis instances create landlord-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x

# Get Redis connection info
gcloud redis instances describe landlord-redis --region=us-central1
```

### 4. Secret Management
Store sensitive data in Secret Manager:

```bash
# Create secrets
echo "your-secret-key" | gcloud secrets create flask-secret-key --data-file=-
echo "your-db-password" | gcloud secrets create db-password --data-file=-
echo "your-sendgrid-key" | gcloud secrets create sendgrid-api-key --data-file=-

# Access secrets in app.yaml
env_variables:
  SECRET_KEY: "projects/PROJECT_ID/secrets/flask-secret-key/versions/latest"
```

### 5. File Storage
The application supports Google Cloud Storage for file uploads:

```bash
# Create storage bucket
gsutil mb gs://your-project-id-media
gsutil iam ch allUsers:objectViewer gs://your-project-id-media

# Update app.yaml
env_variables:
  MEDIA_STORAGE_BACKEND: "gcs"
  GCS_BUCKET: "your-project-id-media"
```

## Features Included

### 🏠 Core Property Management
- Property listings and management
- Task assignment and tracking
- Inventory management
- Calendar integration

### 📱 Interactive Guest Guidebook
- **List View**: `/guest/{property_id}/guidebook?token={token}`
- **Interactive Map**: `/guest/{property_id}/guidebook/map?token={token}`
- Mobile-responsive design
- Token-based secure access
- 12 categories of recommendations

### 🗓️ Worker Calendar System
- **Public Calendar**: `/worker-calendar/{token}`
- **Settings**: `/{property_id}/worker-calendar-settings`
- 4-week horizontal view
- Checkout time emphasis
- Mobile-optimized for field workers

### 🔐 Security Features
- Token-based authentication for public access
- Rate limiting and CSRF protection
- Input validation and sanitization
- Secure file uploads

## Monitoring and Maintenance

### 1. View Logs
```bash
# Real-time logs
gcloud app logs tail

# Specific service logs
gcloud app logs read --service=default --limit=50
```

### 2. Check Application Health
```bash
# Health check endpoint
curl https://your-project-id.appspot.com/health
```

### 3. Database Migrations
```bash
# Run migrations manually
gcloud app exec -- python main.py db upgrade
```

### 4. Scaling Configuration
Update `app.yaml` for scaling:
```yaml
automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check Cloud SQL instance is running
   - Verify connection string format
   - Ensure App Engine has Cloud SQL access

2. **Static Files Not Loading**
   - Verify static file handlers in `app.yaml`
   - Check file paths in templates
   - Ensure files exist in `app/static/`

3. **Environment Variables Not Set**
   - Check `app.yaml` env_variables section
   - Verify Secret Manager permissions
   - Use `gcloud app describe` to check config

4. **Memory/CPU Issues**
   - Increase resources in `app.yaml`
   - Check application logs for memory errors
   - Consider optimizing database queries

### Getting Help

1. **View Application Logs**
   ```bash
   gcloud app logs tail --service=default
   ```

2. **Check Build Logs**
   ```bash
   gcloud builds list --limit=5
   gcloud builds log BUILD_ID
   ```

3. **Debug Database Issues**
   ```bash
   gcloud sql operations list --instance=your-instance
   ```

## Production Checklist

- [ ] Update all environment variables in `app.yaml`
- [ ] Set up Cloud SQL instance and database
- [ ] Configure Redis for caching (optional)
- [ ] Set up file storage bucket
- [ ] Configure email service (SendGrid/SMTP)
- [ ] Set up monitoring alerts
- [ ] Configure custom domain (optional)
- [ ] Set up SSL certificate (automatic with custom domain)
- [ ] Configure backup strategy
- [ ] Review security settings
- [ ] Test all features end-to-end

## Cost Estimation

### App Engine Standard Environment
- **F1 instance**: ~$0.05/hour (minimal usage)
- **F2 instance**: ~$0.10/hour (moderate usage)

### Additional Services
- **Cloud SQL (db-f1-micro)**: ~$7.67/month
- **Cloud Storage**: ~$0.02/GB/month
- **Redis (1GB)**: ~$45/month (optional)

### Traffic-Based Costs
- Requests: First 28 instance-hours free daily
- Outbound bandwidth: $0.12/GB

Total estimated monthly cost for small deployment: **$15-50/month**

## Support

For deployment issues:
1. Check this guide first
2. Review Google Cloud documentation
3. Check application logs
4. Contact support if needed

---

*This deployment guide is based on the example-cloud structure and adapted for the Short Term Landlord Flask application.*