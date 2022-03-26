'''
    This script reads all the raw timestamp files for a scan, and saves a raw histogram image for that file
    If the raw histogram image already exists, this script does nothing
'''
#### Standard Library Imports
import glob
import os

#### Library imports
import numpy as np
import matplotlib.pyplot as plt
from IPython.core import debugger
breakpoint = debugger.set_trace

#### Local imports
from scan_data_utils import *
from pileup_correction import *
from read_hydraharp_outfile_t3 import *
from read_positions_file import read_positions_file, get_coords, POSITIONS_FNAME
from research_utils.timer import Timer
from research_utils.plot_utils import *
# from toflib.coding import IdentityCoding, GrayCoding, TruncatedFourierCoding, WalshHadamardCoding, WalshHadamardBinaryCoding
from research_utils.io_ops import load_json, write_json

def update_scene_scan_params(scan_params, scene_id, n_rows_fullres, n_cols_fullres):
    if(scene_id in scan_params["scene_params"].keys()):
        # Swap rows and cols to transpose image
        scan_params["scene_params"][scene_id]["n_rows_fullres"] = n_cols_fullres
        scan_params["scene_params"][scene_id]["n_cols_fullres"] = n_rows_fullres
    else:
        # Swap rows and cols to transpose image
        scan_params["scene_params"][scene_id] = scan_params["scene_params"]["default"]
        scan_params["scene_params"][scene_id]["n_rows_fullres"] = n_cols_fullres
        scan_params["scene_params"][scene_id]["n_cols_fullres"] = n_rows_fullres
    write_json("scan_params.json", scan_params)


if __name__=='__main__':
    
    ## Load parameters shared by all
    scan_data_params = load_json('scan_params.json')
    io_dirpaths = load_json('io_dirpaths.json')
    timestamp_data_base_dirpath = io_dirpaths['timestamp_data_base_dirpath']
    hist_data_base_dirpath = io_dirpaths['hist_data_base_dirpath']
    os.makedirs(hist_data_base_dirpath, exist_ok=True)

    lres_mode = False # Load a low-res version of the image
    lres_factor = 1 # Load a low-res version of the image
    overwrite_hist_img = False
    timestamp_data_base_dirpath = io_dirpaths['timestamp_data_base_dirpath']

    ## Set scene that will be processed 
    # scene_id = '20190209_deer_high_mu/free'
    # scene_id = '20190209_deer_high_mu/det'
    # scene_id = '20190209_deer_high_mu/ext'
    # scene_id = '20190209_deer_high_mu/ext_5%'
    # scene_id = '20181112_blocks/extreme_flux'
    # scene_id = '20181105_tajmahal'
    # scene_id = '20190207_face_scanning_low_mu/free'
    scene_id = '20190207_face_scanning_low_mu/ground_truth'
    # scene_id = '20190207_face_scanning_low_mu/ext_opt_filtering'
    # scene_id = '20190207_face_scanning_low_mu/ext_5%'
    assert(scene_id in scan_data_params['scene_ids']), "{} not in scene_ids".format(scene_id)
    dirpath = os.path.join(timestamp_data_base_dirpath, scene_id)
    hist_dirpath = os.path.join(hist_data_base_dirpath, scene_id)
    os.makedirs(hist_dirpath, exist_ok=True)
    
    ## Read positions data  
    pos_data = read_positions_file(os.path.join(dirpath, POSITIONS_FNAME))
    (x_coords, y_coords) = get_coords(pos_data)
    n_rows_fullres = y_coords.size
    n_cols_fullres = x_coords.size
    update_scene_scan_params(scan_data_params, scene_id, n_rows_fullres, n_cols_fullres)

    ## Get list of all files in the directory, and the scan parameters
    fpaths_list = glob.glob(os.path.join(dirpath, 't3mode_*_*_*.out'))
    fnames_list = [os.path.basename(fpath) for fpath in fpaths_list]
    n_params_in_fname = count_params_in_fname(fnames_list[0])
    assert(n_params_in_fname == 3), 'Invalid fname {}. Expected fname with 3 params'.format(fnames_list[0])
    scan_pos_indeces = np.array([parse_scan_pos_idx(fname) for fname in fnames_list])
    is_long_cable_flags = np.array([parse_is_long_cable_flag(fname) for fname in fnames_list])
    delay_param_list = np.array([parse_delay_param(fname) for fname in fnames_list])

    ## sort the filenames to match the pos data
    sort_indeces = np.argsort(scan_pos_indeces)
    scan_pos_indeces = scan_pos_indeces[sort_indeces]
    is_long_cable_flags = is_long_cable_flags[sort_indeces]  
    delay_param_list = delay_param_list[sort_indeces] 
    fpaths_list = [fpaths_list[sort_idx] for sort_idx in sort_indeces]  
    fnames_list = [fnames_list[sort_idx] for sort_idx in sort_indeces]

    ## Change all vectors into images to know exactly which pixel corresponds to each ID
    fpaths_img = vector2img(np.array(fpaths_list), n_rows_fullres, n_cols_fullres)
    fnames_img = vector2img(np.array(fnames_list), n_rows_fullres, n_cols_fullres)
    scan_pos_indeces_img = vector2img(scan_pos_indeces, n_rows_fullres, n_cols_fullres).astype(np.float32)
    if(lres_mode):
        fpaths_img = fpaths_img[0::lres_factor,0::lres_factor] 
        fnames_img = fnames_img[0::lres_factor,0::lres_factor] 
        scan_pos_indeces_img = scan_pos_indeces_img[0::lres_factor,0::lres_factor]
    (nr, nc) = fnames_img.shape

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

    ## allocate histogram image
    n_data_files = len(fpaths_list)
    n_scan_points = np.min([pos_data.shape[0], n_data_files])
    assert(n_data_files >= pos_data.shape[0]), "Number of data files needs to be >= number of positions"
    print("n data files = {}".format(n_data_files))
    print("n positions = {}".format(pos_data.shape[0]))
    assert(n_data_files == pos_data.shape[0]), "Number of data files does not match number of points in pos data"
    n_scan_points = len(fpaths_list)
    histograms = np.zeros((n_scan_points, n_hist_bins))
    raw_hist_img = np.zeros((nr, nc, n_hist_bins))
    n_laser_cycles_img = np.zeros((nr, nc))
    n_empty_laser_cycles_img = np.zeros((nr, nc))

    ## Load Raw Hist Image if it exists, otherwise, create it
    raw_hist_img_fname = 'raw-' + get_hist_img_fname(nr, nc, hist_tbin_size, max_tbin)
    raw_hist_img_fpath = os.path.join(hist_dirpath, raw_hist_img_fname)
    raw_hist_img_params_str = raw_hist_img_fpath.split('raw-hist-img_')[-1].split('.npy')[0]
    raw_hist_img_dims = raw_hist_img_params_str.split('_tres-')[0]

    if(os.path.exists(raw_hist_img_fpath) and (not overwrite_hist_img)):
        raw_hist_img = np.load(raw_hist_img_fpath)
    else: 
        # timestamps_arr = []
        # sync_vec_arr = []
        # For each file load tstamps, make histogram, and store in hist_img
        for i in range(nr):
            for j in range(nc):
                fpath = fpaths_img[i,j]
                fname = fnames_img[i,j]
                scan_pos_idx = scan_pos_indeces_img[i,j]
                print("{}, {}".format(scan_pos_idx, fname))
                sync_vec, dtime_vec = read_hydraharp_outfile_t3(fpath)
                # timestamps_arr.append(dtime_vec)
                # sync_vec_arr.append(dtime_vec)
                (counts, bin_edges, bins) = timestamps2histogram(dtime_vec, max_tbin=max_tbin, min_tbin_size=min_tbin_size, hist_tbin_factor=hist_tbin_factor)
                n_laser_cycles_img[i,j] = sync_vec.max()
                n_empty_laser_cycles_img[i,j] = calc_n_empty_laser_cycles(sync_vec)
                # roll_amount = calc_hist_shift(fname, hist_tbin_size)
                roll_amount = 0
                counts = np.roll(counts, int(roll_amount))
                raw_hist_img[i,j,:] = counts
        np.save(raw_hist_img_fpath, raw_hist_img)
        np.save(os.path.join(hist_dirpath, 'n-laser-cycles-img_{}.npy'.format(raw_hist_img_dims)), n_laser_cycles_img)
        np.save(os.path.join(hist_dirpath, 'n-empty-laser-cycles-img_{}.npy'.format(raw_hist_img_dims)), n_empty_laser_cycles_img)
    
    # ## Histogram pre-processing parameters
    # hist_start_time = scan_data_params['hist_preprocessing_params']['hist_start_time'] # in ps. used to crop hist
    # hist_end_time = scan_data_params['hist_preprocessing_params']['hist_end_time'] # in ps. used to crop hist
    # hist_shift_time = scan_data_params['hist_preprocessing_params']['hist_shift_time'] # circshift histograms forward so they are not close to boundary
    # hist_start_bin = time2bin(hist_start_time, hist_tbin_size)
    # hist_end_bin = time2bin(hist_end_time, hist_tbin_size)
    # hist_shift_bin = time2bin(hist_shift_time, hist_tbin_size)
    # hist_img_tau = hist_end_time - hist_start_time

    # ## Pre-process and save hist image
    # # Crop beginning and end to remove system inter-reflections
    # hist_img = raw_hist_img[..., hist_start_bin:hist_end_bin]
    # # Circ shift to move peaks away from 0th bin
    # hist_img = np.roll(hist_img, hist_shift_bin)
    # hist_img_fname = get_hist_img_fname(nr, nc, int(hist_tbin_size), hist_img_tau)
    # np.save(os.path.join(hist_dirpath, hist_img_fname), hist_img)

    ## Save intensity image
    plt.clf()
    plt.imshow(raw_hist_img.sum(axis=-1))
    nphotons_img_fname = raw_hist_img_fname.replace('raw-hist-img', 'raw-nphotons-img')
    plt.title(nphotons_img_fname)
    plt.pause(0.1)
    # save_currfig_png(hist_dirpath, nphotons_img_fname)
    plt.pause(0.1)
    # save_img(raw_hist_img.sum(axis=-1), hist_dirpath, nphotons_img_fname )
    plt.clf()
    plt.imshow(raw_hist_img.max(axis=-1))
    maxpeak_img_fname = raw_hist_img_fname.replace('raw-hist-img', 'raw-maxpeak-img')
    plt.title(maxpeak_img_fname)
    plt.pause(0.1)
    # save_currfig_png(hist_dirpath, maxpeak_img_fname)
    plt.pause(0.1)
    # save_img(raw_hist_img.sum(axis=-1), hist_dirpath, maxpeak_img_fname )

    
    plt.clf()
    plt.imshow(raw_hist_img.argmax(axis=-1))
    argmax_img_fname = raw_hist_img_fname.replace('raw-hist-img', 'raw-argmax-img')
    plt.title(argmax_img_fname)
    plt.pause(0.1)
    # save_currfig_png(hist_dirpath, maxpeak_img_fname)
    plt.pause(0.1)
    # save_img(raw_hist_img.sum(axis=-1), hist_dirpath, maxpeak_img_fname )
