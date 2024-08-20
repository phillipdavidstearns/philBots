# Setting up a bot on X

## Prerequisites

1. An account on [X](https://x.com). Sign up [here](https://x.com/i/flow/signup)
1. MongoDB Community installed
1. Python 3.10+

## Setting up an App with a Developers account on X

1. Login to your X account
1. Navigate to the [Overview]https://developer.x.com/en/portal/projects-and-apps) section of Projects & Apps
1. Click **+ Add Project** and complete the set up flow:
	1. Give the project a name.
	1. Select **Exploring the API** from the "use case" dropdown.
	1. Enter a project description
1. Complete the App set up flow:
	1. Give the App a name.
	1. Copy and securely store these keys (in a password manager). If you use a `.env` file, be sure to set permissions appropriately. For example: `chmod 600 .env` if on a Unix or Linux system.
1. In the App Settings click **Set up** under "User authentication settings"
	1. Under "App permissions" select **Read and write and Direct message** 
	1. Under "Type of App" select **Web App, Automated App or Bot**
	1. Under "App info" enter a **Callback URI / Redirect URL**
	1. Under "App info" enter a **Website URL**
	1. Click **Save**
1. Copy and securely store the **Client ID** and **Client Secret**
1. Click **Done**

## Authorizing your App to obtain OAuth 1.0 access tokens

### Setting up Python

Make sure you're using python 3.10+ by checking the output of: `python3 -V`. Upgrade if necessary.

1. Create a directory for your bot code: `mkdir myXBot`
1. Change into that directory: `cd myXBot`
1. Setup a virtual environment for python: `python3 -m venv venv`
1. Activate the environment: `source venv/bin/activate`
1. Install some dependencies: `pip install python-decouple requests pymongo requests_oauthlib`

* Copy the example code from [here](https://github.com/xdevplatform/Twitter-API-v2-sample-code/blob/main/Manage-Tweets/create_tweet.py) and paste it into a new file named `verifyApp.py`

We're going to gut a rewrite this so that we can verify our app and obtain tokens that can be used with the OAuth 1.0 requests our bot will be making to post on our behalf.

### Let's go ahead and setup our `.env` file:

1. Create the `.env` file: `> .env`
1. Edit `.env` so that it contains the keys we got from previous steps:

```
API_KEY="<your api key goes here>"
API_SECRET="<your api key secret goes here>"
```

1. Edit `verifyApp.py` by adding `from decouple import config` to the top of the file. This imports the config method from python-decouple module to allow easy access to variables stored in the `.env` file.
1. Change the assignment of the environment variables to the consumer_* variables to use the values stored in `.env`:

```python
consumer_key = config('API_KEY')
consumer_secret = config('API_SECRET')
```

1. Remove delcaration and assignment of the `payload` variable
1. After the line `oauth_tokens = oauth.fetch_access_token(access_token_url)` add:

```python
print(f"oauth_tokens: {repr(oauth_tokens)}")
exit()
```

1. Everything below `exit()` can be deleted.
1. Run the script: `python3 verifyApp.py`
1. Copy the url in the terminal and paste into a browser
1. Click **Authorize app**
1. Copy the PIN and enter it into the terminal
1. Add the result to `.env`

```
#OAUTH 1.0

OAUTH1_TOKEN="<value of the 'oauth_token' field>"
OAUTH1_TOKEN_SECRET="<value of the 'oauth_token_secret field'>"
```

### Publish to X 

1. Write `hellowWorld.py` script to make a simple bot post:

```python
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

```

1. Run it: `python3 helloWorld.py`. If successful, you should see:

```json
Response code: 201
{
    "data": {
        "edit_history_tweet_ids": [
            "1823906613448642710"
        ],
        "id": "1823906613448642710",
        "text": "Hello world!"
    }
}
```