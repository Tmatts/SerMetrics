import jwt
import time
import requests
from pprint import pprint  # Import pprint for pretty printing
from simple_salesforce import Salesforce
import pandas as pd

# Salesforce Credentials
PRIVATE_KEY_PATH = "/Users/tonym/private.key" # Private key path for signing JWT
CONSUMER_KEY = "3MVG9QDx8IX8nP5QQxBhWlrFYe0i7FE6sJgmFpRKSwAIrQt3TVWB.gutmZ3Bbn3RS8_py8XMkU5LH5NjVKOf5" # Client/app ID
USERNAME = "t.mattingley@girbau.com"
TOKEN_URL = "https://login.salesforce.com/services/oauth2/token" # Salesforce endpoint for passing my JWT token

class SalesforceJWTAuth:
    def __init__(self):
        self.access_token = None
        self.token_expiry = 0
        self.instance_url = None # Set dynamicaly
        self.api_version = None # Set dynamicaly
        self.headers = None

    def generate_jwt(self):
        """Create a new JWT token."""
        with open(PRIVATE_KEY_PATH, "r") as key_file:
            private_key = key_file.read()

        payload = {
            "iss": CONSUMER_KEY,
            "sub": USERNAME,
            "aud": TOKEN_URL,
            "exp": int(time.time()) + 300  # JWT valid for 5 minutes
        }
        return jwt.encode(payload, private_key, algorithm="RS256")

    def request_access_token(self):
        """Get a new access token from Salesforce."""
        jwt_token = self.generate_jwt()
        response = requests.post(TOKEN_URL, data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_token
        })

        if response.status_code == 200:
            response_data = response.json()
            if "access_token" in response_data:
                self.access_token = response_data["access_token"]
                self.instance_url = response_data["instance_url"]
                self.token_expiry = int(time.time()) + 300  # Token valid for 5 minutes, 1800 = 30 minutes
                self.api_version = response_data.get("api_version")
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
        return Salesforce(instance_url=self.instance_url, session_id=access_token)

class SalesforceRequests:
    def __init__(self, sfobj: SalesforceJWTAuth):
        self.sfobj = sfobj

    def fetch_report(self, report_id: str, api_version: str, include_details: bool = True):
        detail_param = 'includeDetails=true' if include_details else ''
        url = f"{self.sfobj.base_url}analytics/reports/{report_id}?{detail_param}"
        try:
            response = requests.get(url, headers=self.sfobj.headers, timeout=20)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:  # Catch HTTP errors
            print(f"Failed to fetch report {report_id}: {e}")
        except requests.exceptions.RequestException as e:  # Catch network errors
             print(f"Failed to fetch report {report_id}: {e}")
        except Exception as e:  # Catch all other exceptions
            print(f"Failed to fetch report {report_id}: {response.status_code}\n{response.text}")

    def query(self, query):
        return self.sf.query_all(query)

    def query_all(self, query):
        return self.sf.query_all(query)

    def query_one(self, query):
        return self.sf.query(query)

    def get_record(self, object_name, record_id):
        return self.sf.get(object_name, record_id)

    def create_record(self, object_name, data):
        return self.sf.create(object_name, data)

    def update_record(self, object_name, record_id, data):
        return self.sf.update(object_name, record_id, data)

    def delete_record(self, object_name, record_id):
        return self.sf.delete(object_name, record_id)

    def describe_object(self, object_name):
        return self.sf.__getattr__(object_name).describe()

    def describe_global(self):
        return self.sf.describe()

    def get_user_info(self):
        return self.sf.get_user_info()

    def get_limits(self):
        return self.sf.limits()

    def get_recent(self):
        return self.sf.recent()

    def get_versions(self):
        return self.sf.versions()

    def get_resources(self):
        return self.sf.resources()

    def get_sobjects(self):
        return self.sf.get_sobjects()

    def get_metadata(self, object_name):
        return self.sf.__getattr__(object_name).metadata()

    def get_layout(self, object_name, layout_type):
        return self.sf.__getattr__(object_name).layout(layout_type)

    def get_approval_layout(self, object_name):
        return self.sf.__getattr__(object_name).approval_layout()

    def get_describe_layouts(self, object_name):
        return self.sf.__getattr__(object_name).describe_layouts()

    def get_describe_layout(self, object_name, record_type_id):
        return self.sf.__getattr__(object_name).describe_layout(record_type_id)

    def get_describe_layouts_by_record_type(self, object_name, record_type_id):
        return self.sf.__getattr__(object_name).describe_layouts_by_record_type(record_type_id)

    def get_describe_tabs(self, object_name):
        return self.sf.__getattr__(object_name).describe_tabs()

    def get_describe_search_scope_order(self, object_name):
        return self.sf.__getattr__(object_name).describe_search_scope_order()

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
sf_requests = SalesforceRequests(sf)
report_data = sf_requests.fetch_report("00OHq000007fYBBMA2", api_version="v63.0", include_details=False)

invoice_report = SalesforceReportParser(report_data)
invoice_df = invoice_report.to_dataframe()
print(invoice_df.head())
# Example API request
# query = "SELECT Id, Name FROM User WHERE Name = 'Tony Mattingley'"
# users = sf.query_all(query)

# if users["totalSize"] > 0:
#     for record in users["records"]:
#         print(f"{record['Name']}, Id: {record['Id']}")
