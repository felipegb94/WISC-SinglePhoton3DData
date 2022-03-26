'''
    This script uses a high SNR pixel from a pre-processed histogram image and extracts the IRF of that scene
    The data collected by this setup has a bi-modal IRF due to lens inter-reflections which explains the two peaks.

    NOTE: This script may not work well with data acquired in synchronous mode that has pile-up. 
    You may need to correct for pile-up first

    NOTE: The ext_5% when denoised end up with 0 photons everywhere so we need to reduce the amount of denoising
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
from scan_data_utils import irf_dirpath
from scan_data_utils import *
from bimodal2unimodal_hist_img import bimodal2unimodal_crop, get_unimodal_nt
from research_utils.timer import Timer
from research_utils.plot_utils import *
from research_utils.io_ops import load_json
from depth_decoding import IdentityCoding

if __name__=='__main__':
    
    ## Load parameters shared by all
    scan_data_params = load_json('scan_params.json')
    io_dirpaths = load_json('io_dirpaths.json')

    hist_img_base_dirpath = io_dirpaths["preprocessed_hist_data_base_dirpath"]

    ## Load processed scene:
    ## Set scene that will be processed 
    scene_id = '20190207_face_scanning_low_mu/free'
    # scene_id = '20190207_face_scanning_low_mu/det'
    # scene_id = '20190207_face_scanning_low_mu/ground_truth'
    # scene_id = '20190207_face_scanning_low_mu/ext_opt_filtering'
    # scene_id = '20190207_face_scanning_low_mu/ext_5%'
    # scene_id = '20190209_deer_high_mu/free'
    # scene_id = '20190209_deer_high_mu/det'
    # scene_id = '20190209_deer_high_mu/ext'
    # scene_id = '20190209_deer_high_mu/ext_5%'
    scene_id = '20181105_face/low_flux'
    scene_id = '20181105_face/opt_flux'

    assert(scene_id in scan_data_params['scene_ids']), "{} not in scene_ids".format(scene_id)
    hist_dirpath = os.path.join(hist_img_base_dirpath, scene_id)

    out_dirpath = os.path.join(irf_dirpath, scene_id)
    os.makedirs(out_dirpath, exist_ok=True)
    
    ## Get params for scene 
    scan_params = scan_data_params['scene_params'][scene_id]

    ## Set parameters of histogram we want to load
    irf_tres = scan_data_params['min_tbin_size'] # in picosecs
    hist_img_tau = scan_data_params['hist_preprocessing_params']['hist_end_time'] - scan_data_params['hist_preprocessing_params']['hist_start_time']
    hist_img_fname = get_hist_img_fname(scan_params['n_rows_fullres'], scan_params['n_cols_fullres'], irf_tres, hist_img_tau)
    hist_img_fpath = os.path.join(hist_dirpath, hist_img_fname)

    ## Load histogram
    assert(os.path.exists(hist_img_fpath)), "{} does not exist. Make sure to run preprocess_raw_hist_img.py first".format(hist_img_fpath)
    hist_img = np.load(hist_img_fpath)
    (nr,nc,nt) = hist_img.shape
    (tbins, tbin_edges) = get_hist_bins(hist_img_tau, irf_tres)

    ## Apply denoising
    if('ext_5%' in scene_id):
        d_hist_img = gaussian_filter(hist_img, sigma=0.1, mode='wrap', truncate=3)
    else:
        d_hist_img = gaussian_filter(hist_img, sigma=1, mode='wrap', truncate=3)
    min_signal_threshold=1.0

    if('20190207_face_scanning_low_mu' in scene_id):
        (r,c) = (109, 50)
    elif('20190209_deer_high_mu' in scene_id):
        (r,c) = (58, 60)
    else:
        (r,c) = (nr//2, nc//2)

    (r_max,c_max) = np.unravel_index(np.argmax(hist_img.sum(axis=-1)), (nr,nc))
    ## extract selected irf and center it
    irf = d_hist_img[r, c, :]
    irf = np.roll(irf, -1*irf.argmax())

    ## 
    ## Zero out bins with less than scene specific threshold
    irf -= np.median(irf)
    d_hist_img -= np.median(d_hist_img,axis=-1,keepdims=True)
    irf[irf < min_signal_threshold] = 0.
    d_hist_img[d_hist_img < min_signal_threshold] = 0.

    ## Save IRF
    irf_fname = get_irf_fname(irf_tres, hist_img_tau)
    np.save(os.path.join(out_dirpath, irf_fname), irf)

    ## Create uni-modal irf by zero-ing out the second peak OR cropping
    pulse_len = time2bin(scan_data_params['irf_params']['pulse_len'], irf_tres)
    second_pulse_offset = time2bin(scan_data_params['irf_params']['second_pulse_offset'], irf_tres)
    unimodal_nt = get_unimodal_nt(nt, scan_data_params['irf_params']['pulse_len'], irf_tres)
    # Generate uni-modal IRF with the same length as original
    unimodal_irf_samelen = np.array(irf)
    unimodal_irf_samelen[second_pulse_offset:second_pulse_offset+pulse_len] = 0.
    np.save(os.path.join(out_dirpath, "unimodal-"+irf_fname), unimodal_irf_samelen)
    # Generate uni-modal IRF where we crop the second pulse and reduce the length
    unimodal_irf = bimodal2unimodal_crop(irf, first_pulse_start_idx=0, pulse_len=pulse_len, second_pulse_offset=second_pulse_offset)
    unimodal_irf_tau = unimodal_irf.size*irf_tres
    unimodal_irf_fname = get_irf_fname(irf_tres, unimodal_irf_tau)
    np.save(os.path.join(out_dirpath, "unimodal-"+unimodal_irf_fname), unimodal_irf)

    ## Fit a cubic spline function to be able to generate any
    f = fit_irf(irf)
    x_fullres = np.arange(0, nt) * (1./nt) 

    ## reconstruct depths with irf
    coding_obj = IdentityCoding(nt, h_irf=irf, account_irf=True)
    decoded_depths = coding_obj.max_peak_decoding(hist_img, rec_algo_id='matchfilt').squeeze()

    ## Plot some results
    plt.clf()
    plt.pause(0.1)
    plt.subplot(3,3,1)
    plt.imshow(hist_img.sum(axis=-1)); plt.title('Sum of Hist')
    plt.subplot(3,3,2)
    plt.imshow(hist_img.argmax(axis=-1)); plt.title('Argmax')
    plt.subplot(3,3,3)
    plt.imshow(decoded_depths); plt.title('MatchFilt w/ IRF');plt.colorbar()
    plt.subplot(3,1,2)
    plt.plot(hist_img[r,c], linewidth=2, alpha=0.75, label='Raw IRF: {},{}'.format(r,c))
    plt.plot(irf, linewidth=2, alpha=0.75, label='Processed IRF: {},{}'.format(r,c))
    plt.plot(d_hist_img[r+1,c], linewidth=2, alpha=0.75, label='Neighbor Pre-proc IRF: {},{}'.format(r+1,c))
    # plt.plot(d_hist_img[r+1,c+1], linewidth=2, alpha=0.75, label='Neighbor Pre-proc IRF: {},{}'.format(r+1,c+1))
    plt.plot(d_hist_img[93,45], linewidth=2, alpha=0.75, label='Neighbor Pre-proc IRF: {},{}'.format(93,45))
    plt.legend(fontsize=14)
    plt.subplot(3,1,3)
    plt.plot(hist_img[r,c], linewidth=2, alpha=0.75, label='Raw IRF: {},{}'.format(r,c))
    plt.plot(unimodal_irf, linewidth=2, alpha=0.75, label='Crop Uni-modal IRF: {},{}'.format(r,c))
    plt.legend(fontsize=14)



    # results_dirpath = os.path.join(io_dirpaths['results_dirpath'], 'real_data_results/irf_calib')

    # out_fname = 'irf_{}_r-{}-c-{}_tres-{}ps_tlen-{}ps'.format(scene_id.replace('/','--'), r, c, int(irf_tres), int(hist_img_tau))
    # save_currfig_png(results_dirpath, out_fname)
