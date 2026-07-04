# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



/**
 * Foundation Module
 *
 * Enables required Google Cloud APIs and sets quota preferences.
 * This module should be applied first before any other infrastructure.
 */

module "project" {
  source  = "terraform-google-modules/project-factory/google"
  version = "~> 18.0"

  name              = var.project_id
  project_id        = var.project_id
  random_project_id = var.random_project_id
  org_id            = var.org_id
  folder_id         = var.folder_id
  billing_account   = var.billing_account
  activate_apis     = var.gcp_service_list
  deletion_policy   = var.deletion_policy

  disable_services_on_destroy = false
  disable_dependent_services  = false
}

resource "google_project_iam_audit_config" "audit" {
  for_each = var.logging_data_access
  project  = module.project.project_id
  service  = each.key

  dynamic "audit_log_config" {
    for_each = {
      for k, v in each.value : k => v
      if v != null
    }
    content {
      log_type         = audit_log_config.key
      exempted_members = try(audit_log_config.value.exempted_members, [])
    }
  }
}

# Ensure Service Extensions service identity exists
# This is required for IAM bindings in model-armor module
resource "google_project_service_identity" "network_services" {
  provider = google-beta
  project  = var.project_id
  service  = "networkservices.googleapis.com"

  depends_on = [module.project]
}

# Allow time for the Service Extensions service identity to propagate
# before downstream modules attempt to bind IAM roles.
resource "time_sleep" "network_services_identity_propagation" {
  depends_on      = [google_project_service_identity.network_services]
  create_duration = "90s"
}

# Enable Vertex AI API explicitly to control order and avoid race conditions
# in the project module's IAM bindings
resource "google_project_service" "aiplatform" {
  project            = module.project.project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Ensure Vertex AI service identity exists
# This must happen after the API is enabled
resource "google_project_service_identity" "aiplatform" {
  provider = google-beta
  project  = module.project.project_id
  service  = "aiplatform.googleapis.com"

  depends_on = [google_project_service.aiplatform]
}

# Allow time for the AI Platform service identity to propagate before
# binding IAM roles to the service agents.
resource "time_sleep" "aiplatform_identity_propagation" {
  count           = var.enable_psc_interface ? 1 : 0
  depends_on      = [google_project_service_identity.aiplatform]
  create_duration = "60s"
}

resource "google_project_iam_member" "aiplatform_network_admin" {
  count      = var.enable_psc_interface ? 1 : 0
  project    = module.project.project_id
  role       = "roles/compute.networkAdmin"
  member     = "serviceAccount:${google_project_service_identity.aiplatform.email}"
  depends_on = [time_sleep.aiplatform_identity_propagation, time_sleep.wait_for_org_policy]
}

resource "google_project_iam_member" "aiplatform_dns_peer" {
  count      = var.enable_psc_interface ? 1 : 0
  project    = module.project.project_id
  role       = "roles/dns.peer"
  member     = "serviceAccount:${google_project_service_identity.aiplatform.email}"
  depends_on = [time_sleep.aiplatform_identity_propagation, time_sleep.wait_for_org_policy]
}

# The Reasoning Engine service agent (gcp-sa-aiplatform-re) also needs
# network and DNS permissions to create PSC Interface NICs and DNS peering zones.
resource "google_project_iam_member" "aiplatform_re_network_admin" {
  count      = var.enable_psc_interface ? 1 : 0
  project    = module.project.project_id
  role       = "roles/compute.networkAdmin"
  member     = "serviceAccount:service-${module.project.project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
  depends_on = [time_sleep.aiplatform_identity_propagation, time_sleep.wait_for_org_policy]
}

resource "google_project_iam_member" "aiplatform_re_dns_peer" {
  count      = var.enable_psc_interface ? 1 : 0
  project    = module.project.project_id
  role       = "roles/dns.peer"
  member     = "serviceAccount:service-${module.project.project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
  depends_on = [time_sleep.aiplatform_identity_propagation, time_sleep.wait_for_org_policy]
}

# Override Domain Restricted Sharing org policy constraint for the project
# to allow Google-managed service agents to be granted IAM roles.
resource "google_project_organization_policy" "allowed_domains_override" {
  project    = module.project.project_id
  constraint = "constraints/iam.allowedPolicyMemberDomains"

  list_policy {
    allow {
      all = true
    }
  }
}

resource "time_sleep" "wait_for_org_policy" {
  depends_on = [google_project_organization_policy.allowed_domains_override]

  create_duration = "30s"
}
