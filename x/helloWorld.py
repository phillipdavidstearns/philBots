import json
from oauth_helper import oauth

if __name__ == '__main__':
    try:
        payload = { "text": "Hello world!" }

        # Make the request to pubilsh tweet
        if (response := oauth.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
        )).status_code != 201:
            raise Exception(f"Request returned an error: {response.status_code} - {response.text}")

        # Print the response as JSON
        print(json.dumps(response.json(), indent=4, sort_keys=True))
    except Exception as e:
        print(e)
    finally:
        exit()