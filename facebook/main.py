# https://blog.tati.digital/2021/03/29/automating-instagram-posts-with-python-and-instagram-graph-api/

import requests
from decouple import config
import logging
import json
from pymongo import MongoClient
import random
import time

from templates import (
  single_image_template,
  multiple_image_template
)

#================================================================
# Caption Formatters

#================================================================

def buildSingleImageText(mediaObject):
  try:
    url = mediaObject['projectURL'] if mediaObject['projectURL'] else config('DEFAULT_URL', cast=str)
    random.shuffle(mediaObject['tagList'])
    tags = ' '.join(['#' + tag for tag in mediaObject['tagList'][:5]])

    text = single_image_template.format(
      title=mediaObject['projectName'],
      body=f"{ mediaObject['name'] } - { mediaObject['description'] }",
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

def getRandomMediaObject(max_tries=5, post_type=None):

  try:
    tries = 0
    candidates = list(mongo_db['media'].find({'type':'image'}))
    mediaObject = None

    while not mediaObject:

      candidate = random.choice(candidates)

      if time.time() - candidate['lastFBPost'] > (config('POST_COOL_DOWN', cast=float, default=7.0) * 86400):
        mediaObject = candidate

      tries+=1
      if tries >= max_tries:
        break

    logging.info(f"getRandomMediaObject() - tries: {tries} | mediaObject ID: {str(mediaObject['_id'])}, filename: {repr(mediaObject['filename'])}")

  except Exception as e:
    logging.error(f'getRandomMediaObject: {repr(e)}')

  finally:
    return mediaObject

#================================================================
# Upload A Photo
# https://developers.facebook.com/docs/graph-api/reference/page/photos/

def uploadSinglePhoto(image_url=None, caption=None, fb_page_id=None, access_token=None, pubilshed=True):
  try:
    params = {
      'url': image_url,
      'pubilshed': pubilshed,
      'access_token': access_token
    }

    if caption:
      params.update({ 'caption': caption })

    if not (response := requests.post(
      url=f"https://{ config('BASE_URL',cast=str) }/{ config('GRAPH_API_VERSION',cast=str) }/{ fb_page_id }/photos",
      params=params
    )).status_code == 200:

      logging.info(f"response: {response.text}")
        # raise Exception(f'No response from FB!')

    return response.json()

  except Exception as e:
    logging.error(f'uploadSinglePhoto(): {repr(e)}')

#================================================================
# MAIN

if __name__ == "__main__":
  try:

    logging.basicConfig(
      level=config('LOG_LEVEL', default=20, cast=int),
      format='[instaBotGT] - %(levelname)s | %(message)s'
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

    access_token = config('PAGES_ACCESS_TOKEN')
    fb_page_id = config('FACEBOOK_PAGE_ID',cast=str)

    if not (mediaObject := getRandomMediaObject()):
      raise Exception('Failed to retrieve a mediaObject to post')

    if not (text := buildSingleImageText(mediaObject)):
      raise Exception("buildSingleImageText() returned an empty string")

    if not (result := uploadSinglePhoto(
      image_url=mediaObject['url'],
      caption=text,
      fb_page_id=fb_page_id,
      access_token=access_token
    )):
      raise Exception('Failed to create a photo post')

  except Exception as e:
    logging.error(f'__main__(): {repr(e)}')
  finally:
    exit()
