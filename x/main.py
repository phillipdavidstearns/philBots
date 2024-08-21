import logging
import requests
import json
import random
import time
from requests_oauthlib import OAuth1Session
from decouple import config
from base64 import b64encode
from pymongo import MongoClient

from templates import (
  single_image_template,
  multiple_image_template
)

from oauth_helper import oauth

#================================================================

def getRandomMediaObject(max_tries=5):
  try:
    tries = 0
    candidates = list(mongo_db['media'].find({'type':'image'}))
    mediaObject = None

    while not mediaObject:

      candidate = random.choice(candidates)

      if time.time() - candidate['lastXPost'] > (config('POST_COOL_DOWN', cast=float, default=7.0) * 86400):
        mediaObject = candidate

      tries += 1
      if tries >= max_tries:
        break

    logging.info(f"getRandomMediaObject() - tries: { tries } | mediaObject ID: { str(mediaObject['_id']) }, filename: { repr(mediaObject['filename']) }")

  except Exception as e:
    logging.error(f'getRandomMediaObject: { repr(e) }')

  finally:
    return mediaObject

#================================================================

def buildSingleImageText(mediaObject):
  try:
    url = mediaObject['projectURL'] if mediaObject['projectURL'] else config('DEFAULT_URL', cast=str)
    random.shuffle(mediaObject['tagList'])
    tags = ' '.join(['#' + tag for tag in mediaObject['tagList'][:5]])

    text = single_image_template.format(
      title=mediaObject['projectName'],
      body=f"{ mediaObject['name'] } { mediaObject['description'] }",
      url=url,
      tags=tags,
    )
    return text

  except Exception as e:
    logging.error(f'buildSingleImageText: { repr(e) }')
    return None

def buildMultiImageText(mediaObjects):
  try:
    body = ""
    tagList = []

    for i, mediaObject in enumerate(mediaObjects):
      body += f"{i+1}. {mediaObject['name']} - {mediaObject['description']}\n"
      tagList += mediaObject['tagList']

    tagList = list(set(tagList))
    random.shuffle(tagList)
    tags = ' '.join(['#' + tag for tag in tagList[:5]])

    text = multiple_image_template.format(
      title=mediaObjects[0]['projectName'],
      body=body,
      tags=tags
    )
    return text

  except Exception as e:
    logging.error(f'buildMultiImageText: { repr(e) }')
    return None

#================================================================
# MEDIA POST

def mediaPost(mediaObject=None):
  logging.info(f"mediaPost() - mediaObject ID: { str(mediaObject['_id']) }, filename: { repr(mediaObject['filename']) }")

  try:
    #select the first group
    group = random.choice(mediaObject['groupList'])

    #find all other members of the group
    groupMembers = mongo_db['media'].find({ 'groupList' : { '$eq': group } })

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

    text = ""
    media = { 'media_ids' : [] }
    published_mediaObjects = []

    for candidate in candidates:
      if not (upload_result := upload_media(candidate)):
        continue

      if 'media_id_string' in upload_result:
        mongo_db['media'].update_one(
          { 'filename': mediaObject['filename'] },
          { '$set': { 'lastXPost': time.time() } }
        )
        media['media_ids'].append(upload_result['media_id_string'])
        published_mediaObjects.append(candidate)

      # stop once we've reached the max
      if len(media['media_ids']) >= max_media_uploads:
        logging.debug(f'Reached max_media_uploads count: { max_media_uploads }')
        break

    if not media['media_ids']:
      raise Exception('Post has media ids.')
    elif len(media['media_ids']) == 1:
      if not( text := buildSingleImageText(mediaObject)):
        raise Exception("buildSingleImageText() returned an empty string")
    else:
      if not (text := buildMultiImageText(published_mediaObjects)):
        raise Exception("buildMultiImageText() returned an empty string")

    return submit_post(
      text=text,
      media=media
    )

  except Exception as e:
    logging.error(f'mediaPost: {repr(e)}')
    return None

#================================================================

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

#================================================================

def submit_post(text="", media=None):
  logging.info(f"text: {text}")
  logging.info(f"media: {media}")

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

    # Create an instance of the MongoDB client
    # ref: https://pymongo.readthedocs.io/en/stable/api/pymongo/mongo_client.html
    mongo_client = MongoClient(
      host=config('MONGO_URL', cast=str),
      username=config('MONGO_USERNAME', cast=str),
      password=config('MONGO_PASSWORD', cast=str),
      authSource=config('MONGO_AUTH_SOURCE', cast=str),
      authMechanism='SCRAM-SHA-256'
    )

    # Get the instance of the database from the client
    # This will be used to interface with the collections within the database
    mongo_db = mongo_client[config('MONGO_DB')]

    mediaPost(getRandomMediaObject())

  except Exception as e:
    logging.error(f"__main__(): {repr(e)}")
