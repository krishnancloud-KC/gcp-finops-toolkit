# gcp-finops-toolkit

![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FinOps](https://img.shields.io/badge/FinOps-Cost_Optimization-green?style=for-the-badge)

> **Cloud cost governance toolkit for GCP** — detect idle resources, automate VM schedules, surface cost anomalies, and enforce budget alerts. All infrastructure managed with Terraform IaC.

Built by **Krishnan C** | Senior Cloud & Data Engineer | 7+ Years GCP/AWS

---

## 💰 What This Toolkit Does

| Feature | Description | Savings Potential |
|---------|-------------|-------------------|
| 🔍 Idle Resource Detector | Finds VMs with <5% CPU, unattached disks, unused IPs | Up to 30% |
| ⏰ VM Scheduler | Auto stop/start VMs outside business hours | Up to 65% |
| 📊 BigQuery Cost Report | Daily/weekly spend by service, SKU, anomaly detection | Visibility |
| 🚨 Budget Alerts | Terraform-managed alerts at 50%, 90%, 100% | Governance |
| 🔄 GitHub Actions CI | Weekly automated reports via Cloud Function | Automation |

---

## 🏗️ Architecture

```
Cloud Scheduler (every Monday 9 AM)
        ↓
Cloud Function (idle-resource-scanner)
        ↓
GCP APIs (Compute + Monitoring + Billing)
        ↓
BigQuery (cost_reports dataset)
        ↓
Looker Studio Dashboard
        ↓
Pub/Sub → Budget Alert Email
```

---

## 📁 Project Structure

```
gcp-finops-toolkit/
├── cost-optimizer/
│   ├── idle_resource_detector.py     # Detect idle VMs, disks, IPs
│   ├── budget_alert_setup.py         # Programmatic budget creation
│   └── rightsizing_recommender.py    # VM rightsizing via Recommender API
├── dashboards/
│   ├── bigquery_cost_report.py       # Cost by service, SKU, anomalies
│   └── looker_studio_template.json   # Ready-to-import dashboard
├── automation/
│   ├── vm_scheduler.py               # Auto start/stop by business hours
│   └── committed_use_analyzer.py     # CUD/SUD savings analysis
├── terraform/
│   ├── main.tf                       # Budget alerts, Cloud Functions, Scheduler
│   └── variables.tf                  # All configurable variables
├── .github/workflows/
│   └── finops-report.yml             # Weekly automated CI report
└── requirements.txt
```

---

## 🚀 Quick Start

### Prerequisites
- GCP Project with billing enabled
- Terraform >= 1.0
- Python 3.11+
- `gcloud` CLI authenticated

### 1. Clone & Install

```bash
git clone https://github.com/krishnancloud-KC/gcp-finops-toolkit.git
cd gcp-finops-toolkit
pip install -r requirements.txt
```

### 2. Configure

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit with your project_id, billing_account_id, alert_email
```

### 3. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 4. Run Idle Resource Scan

```bash
export PROJECT_ID="your-project-id"
python cost-optimizer/idle_resource_detector.py
```

### 5. Enable VM Scheduler

Label your VMs in GCP Console:
```
Key:   finops-schedule
Value: business-hours
```
The scheduler runs every weekday at 8 AM and stops VMs at 6 PM automatically.

---

## 📊 Sample Output

```
============================================================
  GCP FinOps — Idle Resource Report
============================================================
  ⚠️  Idle VM: dev-instance-1    | CPU: 0.8%
  ⚠️  Idle VM: test-worker-3     | CPU: 2.1%
  💾 Unattached disk: old-data-disk (200GB)
  🌐 Unused static IP: 34.102.xxx.xxx (legacy-ip)

  Idle VMs:        2
  Unattached Disks: 1
  Unused Static IPs: 1
✅ Report saved to idle_resource_report.json
```

---

## 🔑 GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `GCP_SA_KEY` | Service account JSON key (Base64) |
| `GCP_PROJECT_ID` | Your GCP project ID |

---

## 🤝 Related Projects

- [mediflow-backend](https://github.com/krishnancloud-KC/mediflow-backend) — Healthcare Claims Data Pipeline (GCP + BigQuery + Terraform)
- [bank-project](https://github.com/krishnancloud-KC/bank-project) — Banking Microservices (Cloud Run + Vertex AI + Terraform)

---

## 👤 Author

**Krishnan C** — Senior Cloud & Data Engineer
- 🌐 GitHub: [@krishnancloud-KC](https://github.com/krishnancloud-KC)
- 💼 Open to: Freelance · Contract · Remote Full-time
- 🛠️ Stack: GCP · AWS · Terraform · FinOps · BigQuery · Python

---

*"Cloud cost optimization is not a one-time task — it's a continuous discipline."*
