"""
GCP VM Scheduler — Auto Start/Stop VMs
Saves up to 65% on compute costs by stopping VMs outside business hours.
Author: Krishnan C | github.com/krishnancloud-KC
"""

from google.cloud import compute_v1
from datetime import datetime
import pytz
import json


PROJECT_ID = "your-gcp-project-id"
TIMEZONE = "America/New_York"

# VMs with label  finops-schedule=business-hours  will be auto-managed
SCHEDULE_LABEL = "finops-schedule"
BUSINESS_HOURS_VALUE = "business-hours"
BUSINESS_START = 8   # 8 AM
BUSINESS_END = 18    # 6 PM
BUSINESS_DAYS = [0, 1, 2, 3, 4]  # Mon–Fri


def is_business_hours() -> bool:
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    return (
        now.weekday() in BUSINESS_DAYS
        and BUSINESS_START <= now.hour < BUSINESS_END
    )


def get_scheduled_vms(project_id: str) -> list:
    client = compute_v1.InstancesClient()
    scheduled = []

    for zone_instances in client.aggregated_list(project=project_id):
        _, scoped = zone_instances
        if scoped.instances:
            for inst in scoped.instances:
                labels = dict(inst.labels) if inst.labels else {}
                if labels.get(SCHEDULE_LABEL) == BUSINESS_HOURS_VALUE:
                    scheduled.append({
                        "name": inst.name,
                        "zone": inst.zone.split("/")[-1],
                        "status": inst.status,
                    })
    return scheduled


def start_vm(project_id: str, zone: str, instance_name: str):
    client = compute_v1.InstancesClient()
    op = client.start(project=project_id, zone=zone, instance=instance_name)
    print(f"  ▶️  Starting: {instance_name} in {zone}")
    return op


def stop_vm(project_id: str, zone: str, instance_name: str):
    client = compute_v1.InstancesClient()
    op = client.stop(project=project_id, zone=zone, instance=instance_name)
    print(f"  ⏹️  Stopping: {instance_name} in {zone}")
    return op


def run_scheduler(project_id: str):
    business_hours = is_business_hours()
    vms = get_scheduled_vms(project_id)
    actions = []

    print(f"\n{'='*60}")
    print(f"  GCP VM Scheduler | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Business hours: {'YES ✅' if business_hours else 'NO ⏹️'}")
    print(f"  Scheduled VMs found: {len(vms)}")
    print(f"{'='*60}")

    for vm in vms:
        if business_hours and vm["status"] == "TERMINATED":
            start_vm(project_id, vm["zone"], vm["name"])
            actions.append({"vm": vm["name"], "action": "STARTED"})

        elif not business_hours and vm["status"] == "RUNNING":
            stop_vm(project_id, vm["zone"], vm["name"])
            actions.append({"vm": vm["name"], "action": "STOPPED"})

        else:
            print(f"  ✅ {vm['name']} — no action needed ({vm['status']})")

    print(f"\n  Actions taken: {len(actions)}")
    return actions


if __name__ == "__main__":
    run_scheduler(PROJECT_ID)
