# This script uses a .tsv (tab-separated values) spreadsheet to update (overwrite)
# existing MongoDB entry data or to insert new entries where none exists
# The assumption is that filenames for media entered into the database are unique (case-sensitive)

import csv
import json
from pymongo import MongoClient

# Python Decouple: Strict separation of settings from code
# https://pypi.org/project/python-decouple/
from decouple import config

# Imports MediaObject from models.py
from models import MediaObject

#================================================================
# Executed while run as a script

if __name__ == '__main__':

  try:

    # Create an instance of the MongoDB client
    # ref: https://pymongo.readthedocs.io/en/stable/api/pymongo/mongo_client.html
    mongo_client = MongoClient(
      host=config('MONGO_URL', cast=str),
      username=config('MONGO_USERNAME', cast=str),
      password=config('MONGO_PASSWORD', cast=str),
      authSource=config('MONGO_DB', cast=str),
      authMechanism='SCRAM-SHA-256'
    )

    # Get the instance of the database from the client
    # This will be used to interface with the collections within the database
    mongo_db = mongo_client[config('MONGO_DB')]

    # NOTE: this script is looking for a file named update.tsv by default
    # override in your .env by adding UPDATE_TSV_PATH="<path/to/your/file.tsv>"
    # Each row of the file will be converted into a dictionary.
    # Fields in the header are mapped to keys.
    # Values are assigned from one row at a time.
    # ref: https://docs.python.org/3/library/csv.html#csv.DictReader
    tsv_file = csv.DictReader(
        open(config('UPDATE_TSV_PATH', cast=str, default='update.tsv')),
        delimiter="\t" #tab seperated
    )

    # Iterate through the rows in tsv_file
    for row in tsv_file:
      # Skip if the row doesn't contain a filename value
      if not 'filename' in row:
        print(f"Row is missing 'filename' field. row: {row}")
        continue
      
      # This step pre-formats some of the data we know that we want to store
      row.update({
        "projectURL": row['projectURL'] if row['projectURL'] else None,
        "url": f"{config('MEDIA_BASE_URL', cast=str)}/{row['filename']}",
        "tagList": json.loads(row['tagList']) if 'tagList' in row else [],
        "groupList": json.loads(row['groupList']) if 'groupList' in row else [],
        "captionList": json.loads(row['captionList']) if 'captionList' in row else []
      })

      # Look for an entry matching this query
      query = { 'filename': row['filename'] }

      # If there an entry for the given filename, update it
      if (find_result := mongo_db['media'].find_one(query)):
        print(f"found mediaObject ID: { str(find_result['_id']) }, filename: { find_result['filename'] }")
        
        row.update({
          "lastIGPost": find_result['lastIGPost'] if 'lastIGPost' in find_result else 0.0,
          "lastXPost": find_result['lastXPost'] if 'lastXPost' in find_result else 0.0,
          "lastFBPost": find_result['lastFBPost'] if 'lastFBPost' in find_result else 0.0,
          "lastLIPost": find_result['lastLIPost'] if 'lastLIPost' in find_result else 0.0,
          "lastTTPost": find_result['lastTTPost'] if 'lastTTPost' in find_result else 0.0
        })

        # This step validates the modified row data
        # NOTES: It discards any keys not in the model without raising an exception.
        # This maintains conformity with the model so junk keys don't make it into the DB entries
        mediaObject = MediaObject(**row)

        # If the update operation was successful, let us know.
        if (update_result := mongo_db['media'].update_one(
          filter=query,
          update={ '$set': mediaObject.model_dump(mode="json") }
        )):
          print(f"documents matched: { update_result.matched_count }, documents modified: { update_result.modified_count }")
          continue

        # Let us know if there was a problem with the update operation
        print(f"Failed to update entry for {mediaObject.filename}")
        continue

      # There wasn't a matching entry for the filename query
      # Validate the row object against the MediaObject model 
      mediaObject = MediaObject(**row)
      # Insert it in the database and let us know if successful
      if (media_object_id := mongo_db['media'].insert_one(mediaObject.model_dump(mode="json")).inserted_id):
        print(f"Entry for {mediaObject['filename']} created. ID: {media_object_id}")
        continue
      # Let us know if the insert operation failed.
      print(f"Failed to create new entry for {mediaObject.filename}")
      continue
    
  except Exception as e:
    print(f"Oops! {repr(e)}")
  finally:
    exit()