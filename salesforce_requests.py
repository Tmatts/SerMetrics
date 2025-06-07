import requests
import pandas as pd

from base_sf_rqst import BaseSalesforceRequest
from salesforce_auth import SalesforceSession


class SalesforceRequests:
    def __init__(self, session: SalesforceSession):
        self.session = session
        self.instance_url = session.instance_url
        self.api_version = session.api_version
        self.headers = {
            "Authorization": f"Bearer {session.access_token}",
            "Content-Type": "application/json",
        }

    def get_report_data(self, report_id: str, include_details: bool = True) -> dict:
        url = f"{self.instance_url}/services/data/v{self.api_version}/analytics/reports/{report_id}?includeDetails={str(include_details).lower()}"
        res = requests.get(url, headers=self.headers)

        if res.status_code == 401:
            raise requests.exceptions.HTTPError(f"Authentication failed: {res.text}")
        elif res.status_code >= 400:
            error_message = f"HTTP {res.status_code}: {res.text}"
            if res.headers.get("Content-Type", "").startswith("application/json"):
                try:
                    error_details = res.json()
                    if isinstance(error_details, list) and error_details:
                        error_message = (
                            f"{error_message} - {error_details[0].get('message', '')}"
                        )
                except ValueError:
                    pass
            raise requests.exceptions.HTTPError(error_message)
        return res.json()

    def run_bulk_query_to_dataframe(
        self, job_request: BaseSalesforceRequest
    ) -> pd.DataFrame:
        # This is a simplified Bulk 2.0 flow
        # You’d normally POST → wait for job → download results
        url = f"{self.instance_url}/services/data/{self.api_version}/jobs/query"
        job_body = {
            "operation": "query",
            "query": job_request,
            "contentType": "JSON",
            "lineEnding": "LF",
        }
        res = requests.post(url, headers=self.headers, json=job_body)
        res.raise_for_status()
        job = res.json()
        job_id = job["id"]

        # Poll for completion
        while True:
            status = requests.get(f"{url}/{job_id}", headers=self.headers).json()
            if status["state"] in ["JobComplete", "Failed", "Aborted"]:
                break

        if status["state"] != "JobComplete":
            raise RuntimeError(f"Bulk job failed: {status}")

        # Get result
        result_url = f"{url}/{job_id}/results"
        result_res = requests.get(result_url, headers=self.headers)
        result_res.raise_for_status()
        data = result_res.json()
        return pd.DataFrame(data)

    def parse_report_to_dataframe(self, report_json: dict) -> pd.DataFrame:
        # Simplified tabular report parser
        columns_meta = report_json["reportMetadata"]["detailColumns"]
        column_info = report_json["reportExtendedMetadata"]["detailColumnInfo"]
        column_labels = [column_info[c]["label"] for c in columns_meta]

        # # Find the correct factMap key
        # fact_map_key = next(iter(report_json["factMap"]), None)
        # # rows = report_json["factMap"][fact_map_key]["rows"]

        all_data = []

        # Iterate through all factMap keys to gather data
        for fact_map_key, fact_map_data in report_json["factMap"].items():
            if "rows" in fact_map_data:
                rows = fact_map_data["rows"]
                data = [
                    [cell.get("label", "") for cell in row["dataCells"]] for row in rows
                ]
                all_data.extend(data)

        return pd.DataFrame(all_data, columns=column_labels)
