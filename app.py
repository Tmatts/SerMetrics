from simple_salesforce import Salesforce
import requests

# Replace with your details
CONSUMER_KEY = "3MVG9QDx8IX8nP5QQxBhWlrFYe0i7FE6sJgmFpRKSwAIrQt3TVWB.gutmZ3Bbn3RS8_py8XMkU5LH5NjVKOf5"
CONSUMER_SECRET = "CCD8BD4A39FB6DAA8B7DB1976979DE49A21DC71FE060C0C2052DE147DCE13ED6"
USERNAME = "tonyma@girbau.co.uk"
PASSWORD = "Radzedes#2741!!"
TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"

# Request Access Token
data = {
    "grant_type": "password",
    "client_id": CONSUMER_KEY,
    "client_secret": CONSUMER_SECRET,
    "username": USERNAME,
    "password": PASSWORD
}
response = requests.post(TOKEN_URL, data=data).json()
print(response)

# Connect to Salesforce
sf = Salesforce(instance_url=response["instance_url"], session_id=response["access_token"])
print("Connected successfully!")