#\!/bin/bash

# Fixed Cloud Run deployment for Short Term Landlord
set -e

PROJECT_ID="speech-memorization"
REGION="us-central1"
SERVICE_NAME="short-term-landlord"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🏠 Deploying Short Term Landlord to Cloud Run (Fixed)..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"

# Set project
gcloud config set project "$PROJECT_ID"

# Build with Cloud Build using Cloud Run specific Dockerfile
echo "Building with Cloud Run Dockerfile..."
gcloud builds submit --tag "$IMAGE_NAME" -f Dockerfile.cloudrun .

# Delete existing service if it exists and is unhealthy
echo "Cleaning up existing unhealthy service..."
gcloud run services delete "$SERVICE_NAME" --region "$REGION" --quiet || echo "Service doesn't exist, continuing..."

# Deploy to Cloud Run with proper configuration
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
    --timeout 3600 \
    --set-env-vars "DATABASE_URL=sqlite:////tmp/app.db,GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,FLASK_ENV=production"

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
echo "✅ Deployment complete\!"
echo "Service URL: $SERVICE_URL"

echo "🧪 Testing deployment..."
sleep 10
if curl -f -s "$SERVICE_URL/" > /dev/null; then
    echo "✅ Service is responding\!"
else
    echo "⚠️  Service might still be starting up"
fi

echo "Admin credentials:"
echo "Username: issac@alfaren.xyz"
echo "Password: Dashboard_Admin123\!"
EOF < /dev/null