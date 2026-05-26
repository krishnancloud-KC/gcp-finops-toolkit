terraform {
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

# ── Budget Alert — Monthly Threshold ──────────────────────────────────────────
resource "google_billing_budget" "monthly_budget" {
  billing_account = var.billing_account_id
  display_name    = "Monthly GCP Budget Alert"

  budget_filter {
    projects = ["projects/${var.project_number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget_usd)
    }
  }

  # Alert at 50%, 90%, 100%
  threshold_rules {
    threshold_percent = 0.5
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 0.9
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    pubsub_topic                     = google_pubsub_topic.budget_alerts.id
    schema_version                   = "1.0"
    monitoring_notification_channels = [google_monitoring_notification_channel.email_alert.name]
    disable_default_iam_recipients   = false
  }
}

# ── Pub/Sub Topic for Budget Alerts ──────────────────────────────────────────
resource "google_pubsub_topic" "budget_alerts" {
  name    = "finops-budget-alerts"
  project = var.project_id
}

# ── Email Notification Channel ────────────────────────────────────────────────
resource "google_monitoring_notification_channel" "email_alert" {
  display_name = "FinOps Budget Alert Email"
  type         = "email"
  project      = var.project_id

  labels = {
    email_address = var.alert_email
  }
}

# ── Cloud Function to handle budget breaches ─────────────────────────────────
resource "google_cloudfunctions2_function" "budget_handler" {
  name     = "finops-budget-handler"
  location = var.region
  project  = var.project_id

  build_config {
    runtime     = "python311"
    entry_point = "handle_budget_alert"

    source {
      storage_source {
        bucket = google_storage_bucket.finops_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "256M"
    timeout_seconds    = 60

    environment_variables = {
      PROJECT_ID = var.project_id
      ALERT_EMAIL = var.alert_email
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.budget_alerts.id
  }
}

# ── GCS Bucket for Cloud Function source ─────────────────────────────────────
resource "google_storage_bucket" "finops_source" {
  name     = "${var.project_id}-finops-source"
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition { age = 30 }
    action    { type = "Delete" }
  }
}

resource "google_storage_bucket_object" "function_source" {
  name   = "budget_handler.zip"
  bucket = google_storage_bucket.finops_source.name
  source = "${path.module}/functions/budget_handler.zip"
}

# ── Cloud Scheduler — Daily Idle Resource Scan ────────────────────────────────
resource "google_cloud_scheduler_job" "idle_scan" {
  name      = "finops-idle-resource-scan"
  region    = var.region
  project   = var.project_id
  schedule  = "0 9 * * 1"   # Every Monday 9 AM
  time_zone = "America/New_York"

  http_target {
    uri         = google_cloudfunctions2_function.idle_scanner.url
    http_method = "POST"

    oidc_token {
      service_account_email = google_service_account.finops_sa.email
    }
  }
}

# ── Service Account for FinOps automation ─────────────────────────────────────
resource "google_service_account" "finops_sa" {
  account_id   = "finops-automation-sa"
  display_name = "FinOps Automation Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "finops_compute_viewer" {
  project = var.project_id
  role    = "roles/compute.viewer"
  member  = "serviceAccount:${google_service_account.finops_sa.email}"
}

resource "google_project_iam_member" "finops_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.finops_sa.email}"
}
