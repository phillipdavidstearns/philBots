# Imports MediaType from enums.py
from enums import MediaType
from pydantic import BaseModel, HttpUrl

# MediaObject is a subclass of pydantic's BaseModel.
# This model defines how media is structured in the database.
# Data type specification and validation are now possible.
# Note the use of the MediaType class for 'type'
# ref: https://docs.pydantic.dev/latest/api/base_model/

class MediaObject(BaseModel):
  name: str
  description: str = ""
  filename: str
  type: MediaType
  url: HttpUrl
  projectName: str = ""
  projectURL: HttpUrl | None = None
  description: str = ""
  lastIGPost: float
  lastXPost: float
  lastFBPost: float
  lastLIPost: float
  lastTTPost: float
  tagList : list[str] = []
  groupList : list[str] = []
  captionList : list[str] = []
