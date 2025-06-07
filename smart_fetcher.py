from salesforce_requests import SalesforceRequests
import pandas as pd
# -*- coding: utf-8 -*-


class SmartReportFetcher:
    def __init__(self, sf: SalesforceRequests):
        self.sf = sf

    def fetch_report_data(self, report_id: str) -> pd.DataFrame:
        """
        Try the Reports API first. If 2000-row limit is hit, fall back to Bulk 2.0.
        """
        try:
            report_json = self.sf.get_report_data(report_id)
            rows = report_json.get("factMap", {}).get("T!T", {}).get("rows", [])
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve report via Reports API: {e}")

        if len(rows) < 2000:
            print(f"✅ Used Reports API: {len(rows)} rows")
            return self.sf.parse_report_to_dataframe(report_json)

        print("⚠️  Reports API row limit hit — falling back to Bulk 2.0")
        soql = self.get_soql_fallback(report_id)
        return self.sf.run_bulk_query_to_dataframe(soql)

    def get_soql_fallback(self, report_id: str) -> str:
        fallback_map = {
            "00OHq000007fYBBMA2": "SELECT Id, Name, CreatedDate FROM Contact"
            # Add more mappings here
        }
        if report_id not in fallback_map:
            raise ValueError(f"No fallback SOQL defined for report {report_id}")
        return fallback_map[report_id]
