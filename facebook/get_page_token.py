import requests
import json
from decouple import config

#================================================================
# Get page access token:
# https://developers.facebook.com/docs/marketing-api/system-users/guides/api-calls

def getPageAccessToken(access_token=None):
  params = {
    'access_token': access_token
  }

  response = requests.get(
    url=f"https://{ config('BASE_URL') }/{ config('GRAPH_API_VERSION') }/me/accounts",
    params=params
  )

  return response.json()

if __name__ == '__main__':
  result = getPageAccessToken(config('SYSTEM_USER_TOKEN', cast=str))
  print(f"result: { json.dumps(result, indent=4) }")