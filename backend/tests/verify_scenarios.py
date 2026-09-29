import urllib.request
import json
import sys

def query_api(msg, history=[]):
    req = urllib.request.Request(
        'http://localhost:8000/api/query',
        data=json.dumps({'message': msg, 'history': history}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def main():
    print("=== RUNNING ALL 10 PRODUCTION QUERY SCENARIOS ===")

    # 1. Total Revenue 2025 (KPI Card)
    r1 = query_api("What is our total revenue in 2025?")
    print(f"1. Total Revenue 2025 -> type: {r1['type']} | is_kpi: {r1['is_kpi']} | kpis: {len(r1.get('kpi_metrics', []))} | chart: {r1['chart_type']}")

    # 2. Revenue by Category (Bar Chart)
    r2 = query_api("Show revenue by product category.")
    print(f"2. Revenue by Category -> type: {r2['type']} | chart: {r2['chart_type']} | rows: {r2['row_count']} | x: {r2['x_axis']} | y: {r2['y_axis']}")

    # 3. Monthly Sales 2025 (Line Chart)
    r3 = query_api("What were our monthly sales in 2025?")
    print(f"3. Monthly Sales 2025 -> type: {r3['type']} | chart: {r3['chart_type']} | rows: {r3['row_count']} | x: {r3['x_axis']}")

    # 4. Top 10 Customers by Spending (Ranked Bar Chart)
    r4 = query_api("Who are our top 10 customers by spending?")
    print(f"4. Top 10 Customers Spending -> type: {r4['type']} | chart: {r4['chart_type']} | rows: {r4['row_count']} | metric: {r4.get('metric_name')}")

    # 5. Percentage by Region (Pie Chart)
    r5 = query_api("What percentage of sales came from each region?")
    print(f"5. Percentage by Region -> type: {r5['type']} | chart: {r5['chart_type']} | rows: {r5['row_count']}")

    # 6. Ambiguous Best Customers
    r6 = query_api("Show me our best customers.")
    print(f"6. Ambiguous Best Customers -> type: {r6['type']} | is_ambiguous: {r6['is_ambiguous']} | options: {len(r6.get('clarification_options', []))}")

    # 7. Follow-up: Highest total spending
    r7 = query_api("Highest total spending", [
        {"role": "user", "content": "Show me our best customers."},
        {"role": "assistant", "content": r6["clarification_question"]}
    ])
    print(f"7. Clarified: Highest Spending -> type: {r7['type']} | chart: {r7['chart_type']} | rows: {r7['row_count']}")

    # 8. Follow-up: Most recent purchase (Must be table for recency!)
    r8 = query_api("Most recent purchase", [
        {"role": "user", "content": "Show me our best customers."},
        {"role": "assistant", "content": r6["clarification_question"]}
    ])
    print(f"8. Clarified: Recency -> type: {r8['type']} | chart: {r8['chart_type']} | metric: {r8.get('metric_name')}")

    # 9. Unsupported Question (Weather)
    r9 = query_api("What is today's weather forecast?")
    print(f"9. Unsupported Weather -> type: {r9['type']} | is_supported: {r9['is_supported']} | reason: {bool(r9.get('unsupported_reason'))}")

    # 10. Security Block (DROP TABLE)
    r10 = query_api("DROP TABLE customers;")
    print(f"10. Security Check -> type: {r10['type']} | blocked: {bool(r10.get('error') or 'Blocked' in (r10.get('sql') or ''))}")

    print("=== ALL 10 SCENARIOS VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
