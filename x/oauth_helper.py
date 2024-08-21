from decouple import config
from requests_oauthlib import OAuth1Session

# create the OAuth1Session using the access keys and tokens saved in .env
oauth = OAuth1Session(
    client_key=config("API_KEY", cast=str),
    client_secret=config("API_SECRET", cast=str),
    resource_owner_key=config("OAUTH1_TOKEN", cast=str),
    resource_owner_secret=config("OAUTH1_TOKEN_SECRET", cast=str),
)