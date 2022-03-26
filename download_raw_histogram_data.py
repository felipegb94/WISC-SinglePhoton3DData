'''
    This script downloads the raw timestamp data files for a given scenes 3D scan.
    The raw data folders can be 1 to 9GB in size.
'''

#### Standard Library Imports
import gdown
import zipfile
import os

#### Library imports
import numpy as np
import matplotlib.pyplot as plt
from IPython.core import debugger
breakpoint = debugger.set_trace

#### Local imports
from research_utils import io_ops

def download_and_extract_zip(url, data_base_dirpath, scene_id):
    zip_fpath = os.path.join(data_base_dirpath, '{}.zip'.format(scene_id))
    print("Downloading: {}".format(zip_fpath))
    if(os.path.exists(zip_fpath)):
        print("{} already exists. Aborting download. If you wish to overwrite delete the file. ".format(zip_fpath))
    else:
        gdown.download(url, zip_fpath, fuzzy=True)
        print('Extracting ... this may take a few minutes..')
        with zipfile.ZipFile(zip_fpath, 'r') as f:
            f.extractall(data_base_dirpath)

if __name__=='__main__':

    ## Set scene ID that we want to download
    # See io_dirpaths.json for all options
    ## Scans from async shifting paper
    # scene_id = "20190207_face_scanning_low_mu"
    # scene_id = "20190209_deer_high_mu"
    ## Scans from optimal filterins
    scene_id = "20181105_face"
    # scene_id = "20181112_blocks"

    ## Get dirpath where to download the data
    io_dirpaths = io_ops.load_json('io_dirpaths.json')
    data_base_dirpath = io_dirpaths['hist_data_base_dirpath']
    # Make folder to save data in. 
    os.makedirs(data_base_dirpath, exist_ok=True)

    ## Download file
    gdrive_urls = io_dirpaths["histogram_gdrive_urls"]
    assert(scene_id in gdrive_urls.keys()), "Invalid scene ID"
    scene_url = gdrive_urls[scene_id]

    download_and_extract_zip(scene_url, data_base_dirpath, scene_id)
