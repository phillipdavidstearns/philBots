from enum import Enum

# MediaType is a subclass of Enum.
# It specifies all possible media types to account for and store.
# In this example, only images and video are valid.
# ref: https://docs.python.org/3/library/enum.html

class MediaType(str, Enum):
  IMAGE = "image"
  VIDEO = "video"
