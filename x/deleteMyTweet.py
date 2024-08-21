import argparse
from oauth_helper import oauth
import json

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            prog='Delete My Tweet',
            description='You provide tweet ID and I delete it'
        )

        parser.add_argument('tweet_id', type=str)

        args = parser.parse_args()

        # Making the request
        response = oauth.delete(
            url=f"https://api.twitter.com/2/tweets/{args.tweet_id}",
        )

        # Print the response as JSON
        print(json.dumps(response.json(), indent=4, sort_keys=True))
    except Exception as e:
        print(e)
    finally:
        exit()
