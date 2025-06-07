import requests
from dotenv import load_dotenv
import jwt
import time
import os


class SalesforceJWTAuth:
    def __init__(self):
        """
        Loads Salesforce credentials from environment variables.

        Attributes:
            PRIVATE_KEY_PATH (str): The file path to the private key used for signing JWT.
            CONSUMER_KEY (str): The client/application ID for Salesforce.
            USERNAME (str): The Salesforce username.
            TOKEN_URL (str): The Salesforce endpoint URL for passing the JWT token.
        """
        load_dotenv()  # Load environment variables from .env file

        self.consumer_key = os.getenv("CONSUMER_KEY")
        self.username = os.getenv("USERNAME")
        self.private_key_path = os.getenv("PRIVATE_KEY_PATH")
        # Validate private_key_path
        if not self.private_key_path:
            raise ValueError("PRIVATE_KEY_PATH environment variable is not set.")

        # Ensure the private key path is absolute
        if not os.path.isabs(self.private_key_path):
            self.private_key_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), self.private_key_path
            )
        # Check if the private key file exists
        if not os.path.exists(self.private_key_path):
            raise FileNotFoundError(
                f"Private key file not found at {self.private_key_path}"
            )
        self.token_url = os.getenv("SALESFORCE_TOKEN_URL")

        # Initialize authentication state
        self.access_token = None
        self.instance_url = None

    def _authenticate(self):
        """
        Authenticate with Salesforce using JWT.

        Returns:
            tuple: A tuple containing (access_token, instance_url)
        """
        jwt_token = self._create_jwt()
        response = requests.post(
            url=f"{self.token_url}",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token,
            },
        )
        response.raise_for_status()
        auth_data = response.json()

        # Store the values as attributes
        self.access_token = auth_data["access_token"]
        # Validate access_token and instance_url
        if self.access_token is None:
            raise ValueError("Authentication failed: Access token is None.")
        if "instance_url" not in auth_data:
            raise ValueError(
                "Authentication failed: 'instance_url' not found in response."
            )
        self.instance_url = auth_data["instance_url"]

        # Return the values for backward compatibility
        return self.access_token, self.instance_url

    def create_session(self):
        """
        Authenticate and return a SalesforceSession object.

        Returns:
            SalesforceSession: A configured session object ready for API calls
        """
        if not self.access_token:
            self._authenticate()
        return SalesforceSession(self.access_token, self.instance_url)

    def _create_jwt(self) -> str:
        """Create a new JWT token."""
        with open(str(self.private_key_path), "r") as key_file:
            private_key = key_file.read()

        payload = {
            "iss": self.consumer_key,  # Client ID
            "sub": self.username,
            "aud": self.token_url,  # Audience URL
            "exp": int(time.time()) + 300,  # JWT valid for 5 minutes
        }
        return jwt.encode(payload, private_key, algorithm="RS256")


class SalesforceSession:
    def __init__(self, access_token: str, instance_url: str):
        self.access_token = access_token
        self.instance_url = instance_url
        self.api_version = self._discover_latest_version()

    @classmethod
    def from_authenticator(cls, authenticator: SalesforceJWTAuth):
        """
        Create a session from an authenticator object.

        Args:
            authenticator (SalesforceJWTAuth): An authenticator instance,
                which may or may not have already authenticated

        Returns:
            SalesforceSession: A configured session object
        """
        if not authenticator.access_token or not authenticator.instance_url:
            authenticator._authenticate()
        return cls(authenticator.access_token, authenticator.instance_url)

    def _discover_latest_version(self) -> str:
        url = f"{self.instance_url}/services/data/"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()[-1]["version"]

    def get_headers(self) -> dict:
        """Return headers for Salesforce API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
