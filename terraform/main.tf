terraform {
  required_version = ">= 1.5.0"

  # 1. Remote GCS Backend for state locking
  backend "gcs" {
    bucket = "investment-treasury-ai-tfstate"
    prefix = "terraform/state"
  }

  # 2. Provider requirements
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variable Definitions
variable "project_id" {
  type        = string
  description = "The GCP Project ID"
  default     = "investment-treasury-ai"
}

variable "region" {
  type        = string
  description = "Default GCP deployment region"
  default     = "us-central1"
}

# BigQuery Analytics Dataset
resource "google_bigquery_dataset" "analytics_dataset" {
  dataset_id                 = "dbt_dev_analytics"
  friendly_name              = "Treasury Analytics Dataset"
  description                = "Managed by Terraform - Holds production analytical marts"
  location                   = "US"
  delete_contents_on_destroy = false
}

# Service Account for CI/CD Execution
resource "google_service_account" "agent_sa" {
  account_id   = "treasury-ai-agent-sa"
  display_name = "Treasury AI Agent Execution Service Account"
}

# Assign BigQuery Permissions to SA
resource "google_project_iam_member" "bq_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}
