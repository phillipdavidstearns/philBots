import argparse
from decouple import config
from requests_oauthlib import OAuth1Session
import os
import json

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            prog='Delete My Tweet',
            description='You provide tweet ID and I delete it'
        )

        parser.add_argument('tweet_id', type=str)

        args = parser.parse_args()

        # create the OAuth1Session using the access keys and tokens saved in .env
        oauth = OAuth1Session(
            client_key=config("API_KEY", cast=str),
            client_secret=config("API_SECRET", cast=str),
            resource_owner_key=config("OAUTH1_TOKEN", cast=str),
            resource_owner_secret=config("OAUTH1_TOKEN_SECRET", cast=str),
        )

        # Making the request
        response = oauth.delete(
            url=f"https://api.twitter.com/2/tweets/{args.tweet_id}",
        )

        print(f"Response code: {response.status_code}")

        # Saving the response as JSON
        json_response = response.json()
        print(json.dumps(json_response, indent=4, sort_keys=True))
    except Exception as e:
        print(e)
    finally:
        exit()

