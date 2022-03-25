#### Standard Library Imports
import io
import gdown
import zipfile
import subprocess
import urllib.request
import os

#### Library imports
import numpy as np
import matplotlib.pyplot as plt
from IPython.core import debugger
breakpoint = debugger.set_trace

#### Local imports
from research_utils import io_ops

## Get dirpath where to download the data
io_dirpaths = io_ops.load_json('io_dirpaths.json')
data_base_dirpath = io_dirpaths['data_base_dirpath']

## Set scene ID that we want to download
scene_id = "async_face_scan"

## Download file
gdrive_urls = io_dirpaths["gdrive_urls"]
scene_url = gdrive_urls[scene_id]

print("Downloading: {}".format(scene_url))

gdown.download(scene_url, os.path.join(data_base_dirpath, '{}.zip'.format(scene_id)))
