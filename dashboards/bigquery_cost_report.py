"""
GCP BigQuery Cost Report
Queries billing export to surface top cost drivers by service, project, SKU.
Author: Krishnan C | github.com/krishnancloud-KC
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import json


PROJECT_ID = "your-gcp-project-id"
BILLING_DATASET = "your_billing_dataset"
BILLING_TABLE = "gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX"
LOOKBACK_DAYS = 30


def get_cost_by_service(client: bigquery.Client) -> list:
    query = f"""
    SELECT
        service.description AS service,
        ROUND(SUM(cost), 2) AS total_cost_usd,
        ROUND(SUM(cost) * 100 / SUM(SUM(cost)) OVER (), 2) AS cost_percentage
    FROM `{PROJECT_ID}.{BILLING_DATASET}.{BILLING_TABLE}`
    WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {LOOKBACK_DAYS} DAY)
    GROUP BY service
    ORDER BY total_cost_usd DESC
    LIMIT 10
    """
    results = client.query(query).result()
    return [dict(row) for row in results]


def get_cost_by_sku(client: bigquery.Client) -> list:
    query = f"""
    SELECT
        service.description AS service,
        sku.description AS sku,
        ROUND(SUM(cost), 2) AS total_cost_usd
    FROM `{PROJECT_ID}.{BILLING_DATASET}.{BILLING_TABLE}`
    WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {LOOKBACK_DAYS} DAY)
    GROUP BY service, sku
    ORDER BY total_cost_usd DESC
    LIMIT 20
    """
    results = client.query(query).result()
    return [dict(row) for row in results]


def get_daily_spend_trend(client: bigquery.Client) -> list:
    query = f"""
    SELECT
        DATE(usage_start_time) AS date,
        ROUND(SUM(cost), 2) AS daily_cost_usd
    FROM `{PROJECT_ID}.{BILLING_DATASET}.{BILLING_TABLE}`
    WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {LOOKBACK_DAYS} DAY)
    GROUP BY date
    ORDER BY date ASC
    """
    results = client.query(query).result()
    return [{"date": str(row["date"]), "daily_cost_usd": row["daily_cost_usd"]} for row in results]


def get_anomalies(client: bigquery.Client) -> list:
    query = f"""
    WITH daily AS (
        SELECT
            DATE(usage_start_time) AS date,
            service.description AS service,
            ROUND(SUM(cost), 2) AS daily_cost
        FROM `{PROJECT_ID}.{BILLING_DATASET}.{BILLING_TABLE}`
        WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {LOOKBACK_DAYS} DAY)
        GROUP BY date, service
    ),
    stats AS (
        SELECT
            service,
            AVG(daily_cost) AS avg_cost,
            STDDEV(daily_cost) AS stddev_cost
        FROM daily
        GROUP BY service
    )
    SELECT
        d.date,
        d.service,
        d.daily_cost,
        ROUND(s.avg_cost, 2) AS avg_cost,
        ROUND((d.daily_cost - s.avg_cost) / NULLIF(s.stddev_cost, 0), 2) AS z_score
    FROM daily d
    JOIN stats s USING (service)
    WHERE ABS((d.daily_cost - s.avg_cost) / NULLIF(s.stddev_cost, 0)) > 2
    ORDER BY z_score DESC
    LIMIT 10
    """
    results = client.query(query).result()
    return [dict(row) for row in results]


def run_report():
    client = bigquery.Client(project=PROJECT_ID)

    print("\n" + "="*60)
    print("  GCP FinOps — Cost Report")
    print(f"  Period: Last {LOOKBACK_DAYS} days")
    print("="*60)

    print("\n📊 Cost by Service:")
    by_service = get_cost_by_service(client)
    for s in by_service:
        print(f"  {s['service']:<40} ${s['total_cost_usd']:>10} ({s['cost_percentage']}%)")

    print("\n📈 Daily Spend Trend:")
    trend = get_daily_spend_trend(client)
    for t in trend[-7:]:
        print(f"  {t['date']}  ${t['daily_cost_usd']}")

    print("\n🚨 Cost Anomalies (z-score > 2):")
    anomalies = get_anomalies(client)
    for a in anomalies:
        print(f"  {a['date']} | {a['service']} | ${a['daily_cost']} (avg: ${a['avg_cost']})")

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "lookback_days": LOOKBACK_DAYS,
        "cost_by_service": by_service,
        "daily_trend": trend,
        "anomalies": anomalies,
    }

    with open("cost_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("\n✅ Report saved to cost_report.json")
    return report


if __name__ == "__main__":
    run_report()
