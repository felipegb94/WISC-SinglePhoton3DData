'''
    Preprocess the raw histogram images produced by read_fullscan_hydraharp_t3.py
    Preprocessing Steps:
    * Crop earlier and later time bins in histogram (some of them have undesired reflections)
    * Shift histogram

    NOTE: Make sure to set the hist_preprocessing_params inside scan_params.json correctly. Or tune them until you get what you need.
    The default parameters in the scan_params.json work well for 20190209_deer_high_mu and 20190207_face_scanning_low_mu
'''
#### Standard Library Imports
import os

#### Library imports
import numpy as np
import matplotlib.pyplot as plt
from IPython.core import debugger
breakpoint = debugger.set_trace

#### Local imports
from scan_data_utils import *
from research_utils.plot_utils import *
from research_utils.io_ops import load_json

if __name__=='__main__':
    ## Load parameters shared by all
    scan_data_params = load_json('scan_params.json')
    io_dirpaths = load_json('io_dirpaths.json')
    raw_hist_data_base_dirpath = io_dirpaths['hist_data_base_dirpath']
    preprocessed_hist_data_base_dirpath = io_dirpaths['preprocessed_hist_data_base_dirpath']

    ## Set scene that will be processed 
    scene_id = '20190209_deer_high_mu/free'
    # scene_id = '20190209_deer_high_mu/det'
    # scene_id = '20190209_deer_high_mu/ext'
    # scene_id = '20190209_deer_high_mu/ext_5%'
    # scene_id = '20190207_face_scanning_low_mu/free'
    # scene_id = '20190207_face_scanning_low_mu/det'
    # scene_id = '20190207_face_scanning_low_mu/ground_truth'
    # scene_id = '20190207_face_scanning_low_mu/ext_opt_filtering'
    # scene_id = '20190207_face_scanning_low_mu/ext_5%'
    # scene_id = '20181112_blocks/extreme_flux'
    # scene_id = '20181112_blocks/high_flux'
    # scene_id = '20181112_blocks/med_flux'
    # scene_id = '20181112_blocks/low_flux'
    scene_id = '20181105_face/low_flux'
    # scene_id = '20181105_face/opt_flux'
    assert(scene_id in scan_data_params['scene_ids']), "{} not in scene_ids".format(scene_id)
    
    ## Get dirpaths
    raw_hist_dirpath = os.path.join(raw_hist_data_base_dirpath, scene_id)
    hist_dirpath = os.path.join(preprocessed_hist_data_base_dirpath, scene_id)
    os.makedirs(hist_dirpath, exist_ok=True)

    ## Get parameters for raw hist image
    (nr, nc) = (scan_data_params["scene_params"][scene_id]["n_rows_fullres"], scan_data_params["scene_params"][scene_id]["n_cols_fullres"])

    ## Set histogram parameters
    laser_rep_freq = scan_data_params['laser_rep_freq'] # most data acquisitions were done with a 10MHz laser rep freq
    laser_rep_period = (1. / laser_rep_freq)*1e12 # in picosecs
    dead_time = scan_data_params['dead_time'] # In picoseconds
    max_n_tstamps = int(1e8) # discard timestamps if needed
    max_tbin = laser_rep_period # Period in ps
    min_tbin_size = scan_data_params['min_tbin_size'] # Bin size in ps
    hist_tbin_factor = 1.0 # increase tbin size to make histogramming faster
    hist_tbin_size = min_tbin_size*hist_tbin_factor # increase size of time bin to make histogramming faster
    n_hist_bins = get_nt(max_tbin, hist_tbin_size) 

    ## Load Raw Hist Image if it exists, otherwise, create it
    raw_hist_img_fname = 'raw-' + get_hist_img_fname(nr, nc, hist_tbin_size, max_tbin)
    raw_hist_img_fpath = os.path.join(raw_hist_dirpath, raw_hist_img_fname)
    raw_hist_img_params_str = raw_hist_img_fpath.split('raw-hist-img_')[-1].split('.npy')[0]
    raw_hist_img_dims = raw_hist_img_params_str.split('_tres-')[0]

    ## Load histogram image
    raw_hist_img = np.load(raw_hist_img_fpath)

    ##### BEGIN PRE-PROCESSING

    ## Histogram pre-processing parameters
    hist_start_time = scan_data_params['hist_preprocessing_params']['hist_start_time'] # in ps. used to crop hist
    hist_end_time = scan_data_params['hist_preprocessing_params']['hist_end_time'] # in ps. used to crop hist
    hist_shift_time = scan_data_params['hist_preprocessing_params']['hist_shift_time'] # circshift histograms forward so they are not close to boundary
    hist_start_bin = time2bin(hist_start_time, hist_tbin_size)
    hist_end_bin = time2bin(hist_end_time, hist_tbin_size)
    hist_shift_bin = time2bin(hist_shift_time, hist_tbin_size)
    hist_img_tau = hist_end_time - hist_start_time

    ## Pre-process and save hist image
    # Crop beginning and end to remove system inter-reflections
    hist_img = raw_hist_img[..., hist_start_bin:hist_end_bin]
    # Circ shift to move peaks away from 0th bin
    hist_img = np.roll(hist_img, hist_shift_bin)
    hist_img_fname = get_hist_img_fname(nr, nc, int(hist_tbin_size), hist_img_tau)
    np.save(os.path.join(hist_dirpath, hist_img_fname), hist_img)

    ## Plot center histogram
    plt.clf()
    plt.subplot(2,1,1)
    plt.plot(hist_img[nr//2, nc//2,:])
    plt.title("Center Pixel Histogram")
    plt.subplot(2,1,2)
    plt.imshow(np.argmax(hist_img, axis=-1))
    plt.title("Argmax of histogram image")