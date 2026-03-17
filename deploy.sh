#!/bin/bash

# Configuration - EDIT THESE BEFORE RUNNING
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="tho-agent-backend"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

function deploy_backend {
    echo "========================================"
    echo "Deploying BACKEND to Cloud Run..."
    echo "========================================"
    
    echo "Building container image..."
    gcloud builds submit --tag $IMAGE_NAME ./my_config_agent
    
    echo "Deploying to Cloud Run..."
    gcloud run deploy $SERVICE_NAME \
        --image $IMAGE_NAME \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_LOCATION=$REGION
        
    echo "Backend deployment complete!"
}

function deploy_frontend {
    echo "========================================"
    echo "Deploying FRONTEND to Firebase..."
    echo "========================================"
    
    cd frontend
    echo "Building React app..."
    npm run build
    
    echo "Deploying to Firebase Hosting..."
    firebase deploy --only hosting
    cd ..
    
    echo "Frontend deployment complete!"
}

if [ "$1" == "backend" ]; then
    deploy_backend
elif [ "$1" == "frontend" ]; then
    deploy_frontend
elif [ "$1" == "all" ]; then
    deploy_backend
    deploy_frontend
else
    echo "Usage: ./deploy.sh [backend|frontend|all]"
fi
