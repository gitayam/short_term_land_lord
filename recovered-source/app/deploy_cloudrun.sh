#\!/bin/bash

# Short Term Landlord - Cloud Run Deployment Script
set -e

PROJECT_ID="speech-memorization"
REGION="us-central1"
SERVICE_NAME="short-term-landlord"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🏠 Deploying Short Term Landlord to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"

# Set project
gcloud config set project "$PROJECT_ID"

# Enable APIs
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build with Cloud Build
echo "Building image with Cloud Build..."
gcloud builds submit --tag "$IMAGE_NAME" .

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars "DATABASE_URL=sqlite:////tmp/app.db,GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,FLASK_ENV=production"

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
echo "✅ Deployment complete\!"
echo "Service URL: $SERVICE_URL"
EOF < /dev/null