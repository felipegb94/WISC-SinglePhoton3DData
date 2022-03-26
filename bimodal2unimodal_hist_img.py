'''
    Take the histogram images with bimodal signal, and turn them into unimodal signal
    The bimodal signal observed in our data is due to imperfect alignment and it is not very common.
'''
#### Standard Library Imports
import os
import sys
sys.path.append('./tof-lib')

#### Library imports
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from IPython.core import debugger
breakpoint = debugger.set_trace

#### Local imports
from scan_data_utils import *
from research_utils.timer import Timer
from research_utils.plot_utils import *
from depth_decoding import IdentityCoding
from research_utils.io_ops import load_json

def bimodal2unimodal_crop_inplace(bimodal_hist, unimodal_hist, first_pulse_start_idx, pulse_len, second_pulse_offset):
    '''
        In-place bimodal2unimodal crop operation. Crops second peak from bimodal, and then stitches the two remaining arrays together.
    '''
    assert(bimodal_hist.ndim==1), "Only works for 1 dim hist"
    assert(unimodal_hist.ndim==1), "Only works for 1 dim hist"
    nt = bimodal_hist.shape[-1]
    unimodal_nt = nt - pulse_len
    assert(unimodal_hist.shape[-1] == unimodal_nt), "unimodal_hist should have dims of bimodal_hist.size - pulse_len"
    second_pulse_start_idx = (first_pulse_start_idx + second_pulse_offset) % nt
    second_pulse_end_idx = (second_pulse_start_idx + pulse_len) % nt
    try:
        if((first_pulse_start_idx < second_pulse_start_idx) and (first_pulse_start_idx < second_pulse_end_idx)):
            unimodal_hist[0:second_pulse_start_idx] = bimodal_hist[0:second_pulse_start_idx]
            unimodal_hist[second_pulse_start_idx:] = bimodal_hist[second_pulse_end_idx:]
        elif((first_pulse_start_idx < second_pulse_start_idx)):
            unimodal_hist[:] = bimodal_hist[second_pulse_end_idx:second_pulse_start_idx]
        else:
            unimodal_hist[0:second_pulse_start_idx] = bimodal_hist[0:second_pulse_start_idx]
            unimodal_hist[second_pulse_start_idx:] = bimodal_hist[second_pulse_end_idx:]
    except:
        print("Something went wrong. Check logic...")
        unimodal_hist[:] = np.nan
    return unimodal_hist

def bimodal2unimodal_crop(bimodal_hist, first_pulse_start_idx, pulse_len, second_pulse_offset):
    '''
        bimodal2unimodal crop operation. Crops second peak from bimodal, and then stitches the two remaining arrays together.
        Returns new array
    '''
    nt = bimodal_hist.shape[-1]
    unimodal_nt = nt - pulse_len
    assert(unimodal_nt > 0), "pulse_len cant be larger than nt"
    unimodal_hist = np.zeros((unimodal_nt,), dtype=bimodal_hist.dtype)
    bimodal2unimodal_crop_inplace(bimodal_hist, unimodal_hist, first_pulse_start_idx, pulse_len, second_pulse_offset)
    return unimodal_hist


if __name__=='__main__':
    
    ## Load parameters shared by all
    scan_data_params = load_json('scan_params.json')
    io_dirpaths = load_json('io_dirpaths.json')
    hist_img_base_dirpath = io_dirpaths["preprocessed_hist_data_base_dirpath"]

    ## Load processed scene:
    # scene_id = '20190209_deer_high_mu/free'
    scene_id = '20190207_face_scanning_low_mu/free'
    # scene_id = '20190207_face_scanning_low_mu/ground_truth'
    assert(scene_id in scan_data_params['scene_ids']), "{} not in scene_ids".format(scene_id)
    hist_dirpath = os.path.join(hist_img_base_dirpath, scene_id)

    ## Histogram image params
    downsamp_factor = 1 # Spatial downsample factor
    hist_tbin_factor = 1.0 # increase tbin size to make histogramming faster
    n_rows_fullres = scan_data_params['scene_params'][scene_id]['n_rows_fullres']
    n_cols_fullres = scan_data_params['scene_params'][scene_id]['n_cols_fullres']
    (nr, nc) = (n_rows_fullres // downsamp_factor, n_cols_fullres // downsamp_factor) # dims for face_scanning scene  
    min_tbin_size = scan_data_params['min_tbin_size'] # Bin size in ps
    hist_tbin_size = min_tbin_size*hist_tbin_factor # increase size of time bin to make histogramming faster

    ## Load histogram image
    hist_img_tau = scan_data_params['hist_preprocessing_params']['hist_end_time'] - scan_data_params['hist_preprocessing_params']['hist_start_time']
    hist_img_fname = get_hist_img_fname(nr, nc, hist_tbin_size, hist_img_tau)
    hist_img_fpath = os.path.join(hist_dirpath, hist_img_fname)
    hist_img = np.load(hist_img_fpath)
    nt = hist_img.shape[-1]
    (tbins, tbin_edges) = get_hist_bins(hist_img_tau, hist_tbin_size)
    
    ## Load IRF
    irf_tres = scan_data_params['min_tbin_size'] # in picosecs
    irf = get_scene_irf(scene_id, nt, tlen=hist_img_tau, is_unimodal=False)

    ## Load uni-modal IRF
    unimodal_nt = get_unimodal_nt(nt, scan_data_params['irf_params']['pulse_len'], hist_tbin_size)
    unimodal_hist_tau = unimodal_nt*hist_tbin_size
    unimodal_irf = get_scene_irf(scene_id, nt, tlen=hist_img_tau, is_unimodal=True)

    ## reconstruct depths with irf
    coding_obj = IdentityCoding(nt, h_irf=irf, account_irf=True)

    ## Generate uni-modal hist image    
    pulse_len = time2bin(scan_data_params['irf_params']['pulse_len'], irf_tres)
    second_pulse_offset = time2bin(scan_data_params['irf_params']['second_pulse_offset'], irf_tres)
    unimodal_hist_img = np.zeros((nr,nc,unimodal_nt)).astype(hist_img.dtype)
    denoised_hist_img = gaussian_filter(hist_img, sigma=0.75, mode='wrap', truncate=1)
    accurate_shifts = coding_obj.max_peak_decoding(denoised_hist_img, rec_algo_id='matchfilt').squeeze()
    for i in range(nr):
        for j in range(nc):
            first_pulse_start_idx = accurate_shifts[i,j]
            bimodal2unimodal_crop_inplace(hist_img[i,j], unimodal_hist_img[i,j], first_pulse_start_idx, pulse_len, second_pulse_offset)

    ## Save output unimodal hist img
    unimodal_hist_img_fname = get_hist_img_fname(nr, nc, hist_tbin_size, unimodal_hist_tau, is_unimodal=True)
    unimodal_hist_img_fpath = os.path.join(hist_dirpath, unimodal_hist_img_fname)
    np.save(unimodal_hist_img_fpath, unimodal_hist_img)

