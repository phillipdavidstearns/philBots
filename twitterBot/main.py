import logging
import requests
import json
import random
import time
from requests_oauthlib import OAuth1Session
from decouple import config
from base64 import b64encode
from pymongo import MongoClient

from templates import tweet_template

#================================================================
# MONGO SESSION CLASS

class MongoSession():
  def __init__(self, _url, _username, _password, _database):
    self.client = MongoClient(_url,
      username = _username,
      password = _password,
      authSource = _database,
      authMechanism = 'SCRAM-SHA-256'
    )
    self.db = self.client[_database]
    self.media = self.db['media']

#================================================================
# Helpers

def getRandomMediaObject(max_tries=5):
  try:
    tries = 0
    query = {}

    mediaObject = None
    while not mediaObject:
      count = mongo.media.count_documents(query)
      index = random.randrange(0, count)
      candidate = mongo.media.find(query)[index]

      current_time = time.time()
      if current_time - candidate['lastXPost'] > (config('POST_COOL_DOWN', cast=float, default=7.0) * 86400):
        mediaObject = candidate

      tries += 1
      if tries >= max_tries:
        break

    logging.info(f"getRandomMediaObject() - tries: { tries } | mediaObject ID: { str(mediaObject['_id']) }, filename: { repr(mediaObject['filename']) }")

  except Exception as e:
    logging.error(f'getRandomMediaObject: { repr(e) }')

  finally:
    return mediaObject

def buildTweetText(mediaObject):
  url = mediaObject['projectURL'] if mediaObject['projectURL'] else 'https://phillipstearns.com'
  random.shuffle(mediaObject['tagList'])
  tags = ' '.join(['#' + tag for tag in mediaObject['tagList'][:6]])
  try:
    text = tweet_template.format(
      title=mediaObject['projectName'],
      body=f"{mediaObject['name']} - {mediaObject['description']}",
      url=url,
      tags=tags,
    )
    logging.debug(f'text: { repr(text) }')
    return text

  except Exception as e:
    logging.error(f'buildTweetText: { repr(e) }')
    return None

#================================================================
# MEDIA POST

def mediaPost(mediaObject=None):
  logging.info(f"mediaPost() - mediaObject ID: { str(mediaObject['_id']) }, filename: { repr(mediaObject['filename']) }")

  try:
    #select the first group
    group = random.choice(mediaObject['groupList'])

    #find all other members of the group
    groupMembers = mongo.media.find({ 'groupList' : { '$eq': group } })

    #build a list of candidates
    logging.debug(f'Looking for candidates in group: { group }, groupMembers: { groupMembers }')
    candidates = []
    for candidate in groupMembers:
      # check that the last post was not sooner than the cool down duration
      coolDownCheck = time.time() - candidate['lastXPost'] > (config('POST_COOL_DOWN', cast=float, default=7.0) * 86400)
      # if it passes the cool down check and is not the mediaObject add it to the list
      if candidate['filename'] != mediaObject['filename'] and coolDownCheck:
        candidates.append(candidate)

    # mix them all up
    random.shuffle(candidates)
    # put the mediaObject first
    candidates.insert(0, mediaObject)

    # twitter posts can have 1-4 images
    max_media_uploads = random.randrange(1, 5)

    if max_media_uploads == 1 or len(candidates) == 1:
      if not 'media_id' in (upload_result := upload_media(mediaObject)):
        logging.error('Media upload failed.')
        return None

      if not (media_id := str(upload_result['media_id'])):
        logging.error('Post has media ids.')
        return None

      return submit_post(
        text=buildTweetText(mediaObject),
        media={ 'media_ids' : [ media_id ] }
      )

    # build list of media_ids
    media_ids = []
    for candidate in candidates:
      # stop once we've reached the max
      if len(media_ids) >= max_media_uploads:
        logging.debug(f'Reached max_media_uploads count: { max_media_uploads }')
        break

      if 'media_id' in (upload_result := upload_media(candidate)):
        media_ids.append(str(upload_result['media_id']))

    if not media_ids:
      logging.error('Post has media ids.')
      return None

    return submit_post(
      text=buildTweetText(mediaObject),
      media={ 'media_ids' : media_ids }
    )

  except Exception as e:
    logging.error(f'mediaPost: {repr(e)}')
    return None

def upload_media(mediaObject=None):
  # fetch the image data from the mediaObject url
  if (fetch_response := requests.get(mediaObject['url'])).status_code != 200:
    logging.warning(f"Failed to fetch image data. { fetch_response.status_code } | { fetch_response.content }")
    return None

  # encode base64
  media_data = b64encode(fetch_response.content)

  if (post_response := oauth.post(
    url="https://upload.twitter.com/1.1/media/upload.json",
    data={
      "media_data" : media_data,
      "media_category" : "tweet_image"
    },
    headers={ 'Content-Type': 'application/x-www-form-urlencoded' }
  )).status_code != 200:
    logging.warning(f"Failed to post media to X. { post_response.status_code } | { post_response.content }")
    return None

  return post_response.json()

def submit_post(text="", media=None):
 # Making the request
  payload = { "text" : text }

  if media:
    payload['media'] = media

  if (response := oauth.post(
    "https://api.twitter.com/2/tweets",
    json=payload,
  )).status_code != 201:
    logging.warning(f"Request returned an error: { response.status_code } { response.text }")
    return None

  # Saving the response as JSON
  result = response.json()
  logging.info(f"result: { json.dumps(result, indent=4, sort_keys=True) }")
  return result

#================================================================
# MAIN

if __name__ == '__main__':
  try:

    logging.basicConfig(
      level=config('LOG_LEVEL', default=20, cast=int),
      format='[TWITTER BOT] - %(levelname)s | %(message)s'
    )

    mongo = MongoSession(
      config('MONGO_URL'),
      config('MONGO_USERNAME'),
      config('MONGO_PASSWORD'),
      config('MONGO_DB')
    )

    oauth = OAuth1Session(
      client_key=config("API_KEY", cast=str),
      client_secret=config("API_SECRET", cast=str),
      resource_owner_key=config("OAUTH1_TOKEN", cast=str),
      resource_owner_secret=config("OAUTH1_TOKEN_SECRET", cast=str),
    )

    mediaPost(getRandomMediaObject())

  except Exception as e:
    logging.error(f"__main__(): {repr(e)}")
