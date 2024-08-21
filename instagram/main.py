# https://blog.tati.digital/2021/03/29/automating-instagram-posts-with-python-and-instagram-graph-api/

import requests
from decouple import config
import logging
import json
from pymongo import MongoClient
import random
import time

from templates import (
  single_caption_template,
  carousel_caption_template
)

#================================================================
# Caption Formatters

def buildSingleCaption(mediaObject):
  #build the caption
  try:
    #randomly choose from the available captions
    body = random.choice(mediaObject['captionList'])

    # prepend '#' and join tags into a single string
    tags = ' '.join(['#' + tag for tag in mediaObject['tagList']])

    caption = single_caption_template.format(
      title=mediaObject['projectName'],
      subtitle=f"{mediaObject['name']} - {mediaObject['description']}",
      body=body,
      tags=tags,
    )

    logging.debug(f'buildSingleCaption caption: {repr(caption)}')
    return caption

  except Exception as e:
    logging.error(f'buildSingleCaption: {repr(e)}')
    return None

def buildCarouselCaption(mediaObjects):
  #build the caption
  try:
    body = ""
    tagList = []

    for i, mediaObject in enumerate(mediaObjects):
      body += f"{i+1}. {mediaObject['name']} - {mediaObject['description']}\n\n"
      tagList += mediaObject['tagList']

    body += f"{random.choice(mediaObjects[0]['captionList'])}\n\n"

    tagList = list(set(tagList))
    tags = ' '.join(['#' + tag for tag in tagList])

    caption = carousel_caption_template.format(
      title=mediaObjects[0]['projectName'],
      body=body,
      tags=tags,
    )

    return caption

  except Exception as e:
    logging.error(f'buildCarouselCaption: {repr(e)}')
    return None

#================================================================
# Get Random Media Object

def getRandomMediaObject(max_tries=5, post_type=None):

  try:
    tries = 0
    mediaObject = None
    candidates = list(mongo_db['media'].find({'type':'image'}))
    
    while not mediaObject:
      candidate = random.choice(candidates)

      lastIGPost = candidate['lastIGPost'] if 'lastIGPost' in candidate else 0
      if time.time() - lastIGPost > (config('POST_COOL_DOWN', cast=float, default=7.0) * 86400):
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
# createImageContainer

def createImageContainer(image_url=None, caption=None, ig_user_id=None, access_token=None, is_carousel_item=False):
  creation_id = None

  try:
    params = {
      'image_url': image_url,
      'access_token': access_token,
      'is_carousel_item': is_carousel_item
    }

    if caption:
      params.update({ 'caption': caption })

    response = requests.post(
      url=f"https://{ config('BASE_URL',cast=str) }/{ config('GRAPH_API_VERSION',cast=str) }/{ ig_user_id }/media",
      params=params
    )

    if not 'id' in (result := response.json()):
      raise Exception(f'status code: { response.status_code } - { repr(result) }')

    creation_id = result['id']
    logging.debug(f'createImageContainer() - result: {repr(result)}')

  except Exception as e:
    logging.error(f'createImageContainer(): {repr(e)}')
 
  finally:
    return creation_id

#================================================================
# createCarouselContainer

def createCarouselContainer(children=None, caption=None, ig_user_id=None, access_token=None):
  creation_id = None

  try:
    response = requests.post(
      url=f"https://{ config('BASE_URL',cast=str) }/{ config('GRAPH_API_VERSION',cast=str) }/{ ig_user_id }/media",
      params = {
        'media_type': 'CAROUSEL',
        'caption': caption,
        'children': ','.join(children),
        'access_token': access_token
      }
    )

    if not 'id' in (result := response.json()):
      raise Exception(f'status code: { response.status_code } - { repr(result) }')

    creation_id = result['id']
    logging.debug(f'createCarouselContainer() - result: {repr(result)}')

  except Exception as e:
    logging.error(f'createCarouselContainer(): {repr(e)}')
 
  finally:
    return creation_id

def publishMediaPost(container_id, ig_user_id, access_token):
  creation_id = None

  try:
    #Publish the post
    response = requests.post(
      url=f"https://{config('BASE_URL',cast=str)}/{config('GRAPH_API_VERSION',cast=str)}/{ig_user_id}/media_publish",
      params = {
        'creation_id': container_id,
        'access_token' : access_token
      }
    )

    if not 'id' in (result := response.json()):
      raise Exception(f'{repr(result)}')
    
    creation_id = result['id']
    logging.debug(f'media publish result: {repr(result)}')

  except Exception as e:
    logging.error(f'publishMediaPost: {repr(e)}')

  finally:
    return creation_id

#================================================================
# SINGLE POST

def automatedSinglePost(mediaObject=None, ig_user_id=None, access_token=None):
  logging.info(f"automatedSinglePost() - mediaObject ID: {str(mediaObject['_id'])}, filename: {repr(mediaObject['filename'])}")
  try:

    # create the image container
    if not (image_container_id := createImageContainer(
      image_url=mediaObject['url'],
      ig_user_id=ig_user_id,
      caption=buildSingleCaption(mediaObject),
      access_token=access_token
    )):
      # if unsuccessful, raise and exception to pop out of the try block and log it
      raise Exception('failed to create image container')

    mongo_db['media'].update_one(
      { 'filename': mediaObject['filename'] },
      { '$set': { 'lastIGPost': time.time() } }
    )

    if not (publish_id := publishMediaPost(
      container_id=image_container_id,
      ig_user_id=ig_user_id,
      access_token=access_token
    )):
      raise Exception('failed to publish single post')

    return publish_id

  except Exception as e:
    logging.error(f'automatedSinglePost: {repr(e)}')
    return None

#================================================================
# CAROUSEL POST

def automatedCarouselPost(mediaObject=None, ig_user_id=None, access_token=None):
  logging.info(f"automatedCarouselPost() - mediaObject ID: {str(mediaObject['_id'])}, filename: {repr(mediaObject['filename'])}")

  try:
    #select a group at random from groupList
    group = random.choice(mediaObject['groupList'])

    #find all other members of the group
    groupMembers = mongo_db['media'].find({'groupList' : {'$eq': group}})

    #build a list of mediaObjects
    logging.debug(f'Looking for mediaObjects in group: {group}, groupMembers: {groupMembers}')
    mediaObjectsToPublish = []
    for candidate in groupMembers:
      # check that the last post was not sooner than the cool down duration
      coolDownCheck = time.time() - candidate['lastIGPost'] > (config('POST_COOL_DOWN', cast=float, default=7.0) * 86400)
      # if it passes the cool down check and is not the mediaObject add it to the list
      if candidate['filename'] != mediaObject['filename'] and coolDownCheck:
        mediaObjectsToPublish.append(candidate)

    # if the list of mediaObjects is empty, create a single post using the mediaObject
    if len(mediaObjectsToPublish) == 0:
      logging.debug(f"automatedCarouselPost() - No candidates found. Falling back to single post.")
      if not (publish_id := automatedSinglePost(
        mediaObject=mediaObject,
        ig_user_id=ig_user_id,
        access_token=access_token
      )):
        raise Exception('Fall back to single post failed.')
      return publish_id

    # mix them all up
    random.shuffle(mediaObjectsToPublish)
    # put the mediaObject first
    mediaObjectsToPublish.insert(0, mediaObject)

    # build the children image_containers and save them in a list
    publishedMediaObjects = []
    children = []

    max_children = random.randrange(
      config('CAROUSEL_RANGE_MIN', cast=int, default=2),
      config('CAROUSEL_RANGE_MAX', cast=int, default=11)
    )

    for mediaObject in mediaObjectsToPublish:

      # stop once we've reached the max
      if len(children) >= max_children:
        logging.debug('Reached maximum number of children for carousel post.')
        break

      # create the image container, with a caption incase we have to fall back to a single post
      if (image_container_id := createImageContainer(
        image_url=mediaObject['url'],
        ig_user_id=ig_user_id,
        access_token=access_token,
        caption=buildSingleCaption(mediaObject),
        is_carousel_item=True
      )):
        # set the lastIGPost time to the current time
        mongo_db['media'].update_one(
          { 'filename' : mediaObject['filename'] },
          { '$set': { 'lastIGPost': time.time() } }
        )
        children.append(image_container_id)
        publishedMediaObjects.append(mediaObject)

    if not children:
      raise Exception('Carousel has no children!')
    elif len(children) == 1:
      logging.debug(f"automatedCarouselPost() - Carousel only has one child. Publishing that child")
      if not (publish_id := publishMediaPost(
        container_id=children[0],
        ig_user_id=ig_user_id,
        access_token=access_token
      )):
        raise Exception('Fall back to single post failed.')
      return publish_id

    if not (carousel_caption := buildCarouselCaption(
      mediaObjects=publishedMediaObjects
    )):
      raise Exception('buildCarouselCaption failed')

    if not (carousel_container_id := createCarouselContainer(
      children=children,
      caption=carousel_caption,
      ig_user_id=ig_user_id,
      access_token=access_token,
    )):
      raise Exception('failed to create carousel container')

    if not (publish_id := publishMediaPost(
      container_id=carousel_container_id,
      ig_user_id=ig_user_id,
      access_token=access_token
    )):
      raise Exception('failed to publish carousel')

    return publish_id

  except Exception as e:
    logging.error(f'automatedCarouselPost: {repr(e)}')
    return None

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

    access_token = config('SYSTEM_USER_TOKEN',cast=str)
    access_token_app = f"{config('APP_ID',cast=str)}|{config('APP_SECRET',cast=str)}"
    ig_user_id = config('INSTAGRAM_ACCOUNT_ID',cast=str)

    mediaObject = getRandomMediaObject()

    if mediaObject:
      randPostType = random.random()
      if randPostType < config('CAROUSEL_CHANCE_PERCENT', cast=int, default=20) * 0.01:
        automatedCarouselPost(mediaObject, ig_user_id, access_token)
      else:
        automatedSinglePost(mediaObject, ig_user_id, access_token)

  except Exception as e:
    logging.error(f'Unhandled exception in __main__(): {repr(e)}')
  finally:
    exit()
