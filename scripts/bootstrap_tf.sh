#!/usr/bin/env bash
# Bootstrap script to create GCS backend bucket for Terraform state

PROJECT_ID="investment-treasury-ai"
REGION="us-central1"
BUCKET_NAME="${PROJECT_ID}-tfstate"

echo "Creating Terraform state bucket gs://${BUCKET_NAME}..."
gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access

echo "Bucket created successfully!"
