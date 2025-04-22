import jwt
import time
import requests
from pprint import pprint  # Import pprint for pretty printing
from simple_salesforce import Salesforce
import pandas as pd
import os
from io import BytesIO
from dotenv import load_dotenv
from request_dc import BaseSalesforceRequest

class SalesforceJWTAuth:
    def __init__(self):
        self.access_token = None
        self.token_expiry = 0
        self.instance_url = None # Set dynamicaly
        self.api_version = None # Set dynamicaly
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        self.get_salesforce_credentials()

    def get_salesforce_credentials(self):
        """
        Loads Salesforce credentials from environment variables.

        Attributes:
            PRIVATE_KEY_PATH (str): The file path to the private key used for signing JWT.
            CONSUMER_KEY (str): The client/application ID for Salesforce.
            USERNAME (str): The Salesforce username.
            TOKEN_URL (str): The Salesforce endpoint URL for passing the JWT token.
        """
        load_dotenv()


        self.private_key_path = os.getenv("PRIVATE_KEY_PATH")
        self.private_key_path = os.path.abspath(self.private_key_path)
        if not self.private_key_path:
            raise FileNotFoundError(f"Private key file not found {self.private_key_path}").strip('"')
        self.consumer_key = os.getenv("CONSUMER_KEY")
        self.username = os.getenv("USERNAME")
        self.token_url = os.getenv("TOKEN_URL")

    def get_latest_api_version(self):
        """
        Gets the latest available REST API version for this Salesforce instance.
        """
        if not self.instance_url or not self.access_token:
            raise RuntimeError("You must authenticate before retrieving API version.")

        url = f"{self.instance_url}/services/data/"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        versions = response.json()
        self.api_version = versions[-1]["version"]
        return None

    def generate_jwt(self):
        """Create a new JWT token."""
        with open(self.private_key_path, "r") as key_file:
            private_key = key_file.read()

        payload = {
            "iss": self.consumer_key,
            "sub": self.username,
            "aud": self.token_url,
            "exp": int(time.time()) + 300  # JWT valid for 5 minutes
        }
        return jwt.encode(payload, private_key, algorithm="RS256")

    def request_access_token(self):
        """Get a new access token from Salesforce."""
        jwt_token = self.generate_jwt()
        response = requests.post(self.token_url, data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_token
        })

        if response.status_code == 200:
            response_data = response.json()
            if "access_token" in response_data:
                self.access_token = response_data["access_token"]
                self.instance_url = response_data["instance_url"]
                self.token_expiry = int(time.time()) + 300  # Token valid for 5 minutes, 1800 = 30 minutes
                self.headers = {"Authorization": f"Bearer {self.access_token}"}
                print("✅ New access token obtained.")
                return self.access_token
            else:
                raise requests.exceptions.HTTPError(f"❌ Authentication failed: {response_data}")
        else:
            raise requests.exceptions.RequestException(f"❌ Failed to obtain access token. HTTP {response.status_code}: {response.text}")

    def get_access_token(self):
        """Returns a valid access token, refreshing it if expired."""
        if self.access_token is None or time.time() >= self.token_expiry:
            print("🔄 Refreshing Salesforce access token...")
            return self.request_access_token()
        return self.access_token

    def connect_to_salesforce(self):
        """Connect to Salesforce using the latest access token."""
        access_token = self.get_access_token()
        sf_connection = Salesforce(instance_url=self.instance_url, session_id=access_token)
        self.get_latest_api_version() # Get the latest API version and set instance variable
        return sf_connection

class SalesforceRequests:
    def __init__(self, sf_auth_obj: SalesforceJWTAuth, sf_obj: Salesforce):
        self.instance_url = sf_auth_obj.instance_url
        self.headers = sf_auth_obj.headers
        self.api_version = sf_auth_obj.api_version

    def fetch_report_data(self, report_id: str, include_details: bool = True):
        detail_param = 'includeDetails=true' if include_details else 'includeDetails=false'
        
        """
        Run the report with pagination and return all rows.
        """
        all_rows = []
        page_token = None

        while True:
            try:
                if page_token:
                    url = f"{self.instance_url}/services/data/{self.api_version}/analytics/reports/{report_id}?pageToken={page_token}&includeDetails={detail_param}"
                    response = requests.get(url, headers=self.headers)
                else:
                    url = f"{self.instance_url}/services/data/{self.api_version}/analytics/reports/{report_id}"
                    body = {
                        "reportMetadata": {},
                        "includeDetails": detail_param
                    }
                    response = requests.post(url, headers=self.headers, json=body)

                data = response.json()

                rows = data.get('factMap', {}).get('T!T', {}).get('rows', [])
                all_rows.extend(rows)

                page_token = data.get('pageToken')
                if not page_token:
                    break
            except requests.exceptions.HTTPError as e:  # Catch HTTP errors
                print(f"Failed to fetch report {report_id}: {e}")
            except requests.exceptions.RequestException as e:  # Catch network errors
                print(f"Failed to fetch report {report_id}: {e}")
            except Exception as e:  # Catch all other exceptions
                print(f"Failed to fetch report {report_id}: {response.status_code}\n{response.text}")

        return all_rows, data  # or keep data separately for column headers

class SalesforceReportParser:
    def __init__(self, report_data):
        self.report_data = report_data
        pprint(report_data)
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Converts the report JSON into a pandas DataFrame.
        Assumes it's a tabular report (not summary/matrix).
        """
        try:
            columns_meta = self.report_data['reportMetadata']['detailColumns']
            fact_map = self.report_data['factMap']

            # For tabular reports, data is always in factMap['T!T']
            rows = fact_map['T!T']['rows']

            # Get column labels
            # Get column labels
            column_labels = [
                detail_info.get('label', detail_info.get('name', ''))
                for column_key in columns_meta
                if (detail_info := self.report_data['reportExtendedMetadata']['detailColumnInfo'].get(column_key))
            ]

            # Extract row data
            data = []
            for row in rows:
                values = [cell.get('label', '') for cell in row['dataCells']]
                data.append(values)

            return pd.DataFrame(data, columns=column_labels)

        except KeyError as e:
            raise ValueError(f"Unexpected report format or missing key: {e}")

# Example usage
auth = SalesforceJWTAuth()
sf = auth.connect_to_salesforce()
sf_requests = SalesforceRequests(auth, sf)
report_data = sf_requests.fetch_report_data("00OHq000007fYBBMA2", include_details=False)

invoice_report = SalesforceReportParser(report_data)
invoice_df = invoice_report.to_dataframe()
print(invoice_df.head())
# Example API request
# query = "SELECT Id, Name FROM User WHERE Name = 'Tony Mattingley'"
# users = sf.query_all(query)

# if users["totalSize"] > 0:
#     for record in users["records"]:
#         print(f"{record['Name']}, Id: {record['Id']}")
