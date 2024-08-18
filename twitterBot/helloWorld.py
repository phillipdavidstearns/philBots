from decouple import config
from requests_oauthlib import OAuth1Session
import os
import json

# create the OAuth1Session using the access keys and tokens saved in .env
oauth = OAuth1Session(
    client_key=config("API_KEY", cast=str),
    client_secret=config("API_SECRET", cast=str),
    resource_owner_key=config("OAUTH1_TOKEN", cast=str),
    resource_owner_secret=config("OAUTH1_TOKEN_SECRET", cast=str),
)

payload = { "text": "Hello world!" }

# Making the request
response = oauth.post(
    "https://api.twitter.com/2/tweets",
    json=payload,
)

if response.status_code != 201:
    raise Exception(f"Request returned an error: {response.status_code} - {response.text}")

print(f"Response code: {response.status_code}")

# Saving the response as JSON
json_response = response.json()
print(json.dumps(json_response, indent=4, sort_keys=True))
