# The intent was for this to be used to simultaneously upload remotesly and store in a database all the images and metadata...
# What this is becoming is a tool for updating and managing the database entries for
# media files on the remote server that need to also be uploaded to it.

import csv
import json
import subprocess
import os
from decouple import config
from pymongo import MongoClient


class MongoSession():
  def __init__(self, _url, _username, _password, _database):
    self.client = MongoClient(_url,
      username = _username,
      password = _password,
      authSource = _database,
      authMechanism = 'SCRAM-SHA-1'
    )
    self.db = self.client[_database]
    self.media = self.db['media']

mongo = MongoSession(
  config('MONGO_URL'),
  config('MONGO_USERNAME'),
  config('MONGO_PASSWORD'),
  config('MONGO_DB')
)

tsv_file = csv.DictReader(
    open("update.tsv"),
    delimiter="\t"
)

# printing data line by line
for line in tsv_file:
  # print(f'line: {line}')
  if 'filename' in line:
    mediaObject = {
        "name" : "",
        "projectName": "",
        "description" : "",
        "filename" : "",
        "url" : f"{config('MEDIA_BASE_URL', cast=str)}/{line['filename']}",
        "tagList" : [],
        "lastIGPost" : 0,
        "lastXPost" : 0,
        "lastFBPost" : 0,
        "lastLIPost" : 0,
        "groupList" : [],
        "captionList" : [],
        "projectURL": ""
    }

  if 'tagList' in line:
      line['tagList']=json.loads(line['tagList'])
  if 'captionList' in line:
      line['captionList']=json.loads(line['captionList'])
  if 'groupList' in line:
      line['groupList']=json.loads(line['groupList'])

  mediaObject.update(line)

  find_result = mongo.media.find_one({'filename':mediaObject['filename']})
  if find_result:
    print(f"found mediaObject ID: {str(find_result['_id'])}, filename: {mediaObject['filename']}")

  if not find_result:
    media_object_id = mongo.media.insert_one(mediaObject).inserted_id
    print(media_object_id)
  else:
    if 'lastPost' in find_result:
      mediaObject['lastIGPost'] = find_result['lastPost']
    result = mongo.media.update_one(
      {'filename':mediaObject['filename']},
      {
        '$set':mediaObject,
        '$unset':{'lastPost':'','lastReel':'','singlePostID':''}
      }
    )
    print(result.raw_result)

