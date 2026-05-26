"""
GCP Idle Resource Detector
Detects idle VMs, unused disks, and unattached IPs to reduce cloud waste.
Author: Krishnan C | github.com/krishnancloud-KC
"""

from google.cloud import compute_v1
from google.cloud import monitoring_v3
from datetime import datetime, timedelta
import json


PROJECT_ID = "your-gcp-project-id"
IDLE_CPU_THRESHOLD = 5.0   # % CPU — below this = idle
IDLE_DAYS = 7              # check last 7 days


def get_all_instances(project_id: str) -> list:
    client = compute_v1.InstancesClient()
    instances = []
    for zone_instances in client.aggregated_list(project=project_id):
        zone, scoped = zone_instances
        if scoped.instances:
            for instance in scoped.instances:
                instances.append({
                    "name": instance.name,
                    "zone": zone.split("/")[-1],
                    "status": instance.status,
                    "machine_type": instance.machine_type.split("/")[-1],
                })
    return instances


def get_cpu_utilization(project_id: str, instance_name: str, zone: str) -> float:
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"

    now = datetime.utcnow()
    start = now - timedelta(days=IDLE_DAYS)

    interval = monitoring_v3.TimeInterval(
        end_time={"seconds": int(now.timestamp())},
        start_time={"seconds": int(start.timestamp())},
    )

    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": (
                f'metric.type="compute.googleapis.com/instance/cpu/utilization" '
                f'AND resource.labels.instance_id="{instance_name}"'
            ),
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    values = []
    for series in results:
        for point in series.points:
            values.append(point.value.double_value * 100)

    return sum(values) / len(values) if values else 0.0


def detect_idle_vms(project_id: str) -> list:
    print(f"🔍 Scanning VMs in project: {project_id}")
    instances = get_all_instances(project_id)
    idle_vms = []

    for vm in instances:
        if vm["status"] != "RUNNING":
            continue
        avg_cpu = get_cpu_utilization(project_id, vm["name"], vm["zone"])
        if avg_cpu < IDLE_CPU_THRESHOLD:
            idle_vms.append({
                **vm,
                "avg_cpu_percent": round(avg_cpu, 2),
                "recommendation": "STOP or DELETE — low CPU utilization",
            })
            print(f"  ⚠️  Idle VM: {vm['name']} | CPU: {avg_cpu:.2f}%")

    return idle_vms


def detect_unattached_disks(project_id: str) -> list:
    client = compute_v1.DisksClient()
    unattached = []

    for zone_disks in client.aggregated_list(project=project_id):
        _, scoped = zone_disks
        if scoped.disks:
            for disk in scoped.disks:
                if not disk.users:
                    unattached.append({
                        "name": disk.name,
                        "size_gb": disk.size_gb,
                        "type": disk.type_.split("/")[-1],
                        "recommendation": "DELETE unattached disk to save cost",
                    })
                    print(f"  💾 Unattached disk: {disk.name} ({disk.size_gb}GB)")

    return unattached


def detect_unused_static_ips(project_id: str) -> list:
    client = compute_v1.AddressesClient()
    unused_ips = []

    for region_addresses in client.aggregated_list(project=project_id):
        _, scoped = region_addresses
        if scoped.addresses:
            for addr in scoped.addresses:
                if addr.status == "RESERVED" and not addr.users:
                    unused_ips.append({
                        "name": addr.name,
                        "address": addr.address,
                        "region": addr.region.split("/")[-1],
                        "recommendation": "RELEASE unused static IP ($0.01/hr charge)",
                    })
                    print(f"  🌐 Unused static IP: {addr.address} ({addr.name})")

    return unused_ips


def run_report(project_id: str):
    print("\n" + "="*60)
    print("  GCP FinOps — Idle Resource Report")
    print("="*60)

    idle_vms = detect_idle_vms(project_id)
    unattached_disks = detect_unattached_disks(project_id)
    unused_ips = detect_unused_static_ips(project_id)

    report = {
        "project_id": project_id,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "idle_vms": len(idle_vms),
            "unattached_disks": len(unattached_disks),
            "unused_static_ips": len(unused_ips),
        },
        "idle_vms": idle_vms,
        "unattached_disks": unattached_disks,
        "unused_static_ips": unused_ips,
    }

    with open("idle_resource_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Report saved to idle_resource_report.json")
    print(f"   Idle VMs: {len(idle_vms)}")
    print(f"   Unattached Disks: {len(unattached_disks)}")
    print(f"   Unused Static IPs: {len(unused_ips)}")
    return report


if __name__ == "__main__":
    run_report(PROJECT_ID)
