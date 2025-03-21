import jwt
import time
import requests
from simple_salesforce import Salesforce

# Salesforce Credentials
PRIVATE_KEY_PATH = "/Users/tonym/private.key"
CONSUMER_KEY = "3MVG9QDx8IX8nP5QQxBhWlrFYe0i7FE6sJgmFpRKSwAIrQt3TVWB.gutmZ3Bbn3RS8_py8XMkU5LH5NjVKOf5"
USERNAME = "t.mattingley@girbau.com"
TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"
JWT_URL = "https://login.salesforce.com/services/oauth2/authorize"

class SalesforceJWTAuth:
    def __init__(self):
        self.access_token = None
        self.token_expiry = 0
        self.instance_url = None # Set dynamicaly

    def generate_jwt(self):
        """Create a new JWT token."""
        with open(PRIVATE_KEY_PATH, "r") as key_file:
            private_key = key_file.read()

        payload = {
            "iss": CONSUMER_KEY,
            "sub": USERNAME,
            "aud": JWT_URL,
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
                self.token_expiry = int(time.time()) + 300  # Token valid for 5 minutes 1800 = 30 minutes
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

# Example usage
auth = SalesforceJWTAuth()
sf = auth.connect_to_salesforce()
print("✅ Successfully connected to Salesforce!")

# Example API request
query = "SELECT Id, Name, CurrencyIsoCode FROM Account WHERE CurrencyIsoCode = 'GBP' AND Name LIKE '%(Barchester)'  LIMIT 10"
accounts = sf.query_all(query)

if accounts["totalSize"] > 0:
    for record in accounts["records"]:
        print(f"{record['Name']}")
