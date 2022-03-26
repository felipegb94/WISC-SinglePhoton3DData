#### Standard Library Imports
import os

#### Library imports
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, median_filter
from IPython.core import debugger
breakpoint = debugger.set_trace

#### Local imports
from scan_data_utils import *
from research_utils.timer import Timer
from research_utils.plot_utils import *
from depth_decoding import IdentityCoding
from research_utils.io_ops import load_json
from research_utils import np_utils, improc_ops

depth_offset = 0.0

def depths2xyz(depths, fov_major_axis=40, mask=None):
	(n_rows, n_cols) = depths.shape
	(fov_horiz, fov_vert) = improc_ops.calc_fov(n_rows, n_cols, fov_major_axis)
	(phi_img, theta_img) = improc_ops.calc_spherical_coords(fov_horiz, fov_vert, n_rows, n_cols, is_deg=True)
	depths+=depth_offset
	(x,y,z) = improc_ops.spherical2xyz(depths, phi_img, theta_img)
	zmap = np.array(z)
	if(not (mask is None)):
		(x,y,z) = (x[mask], y[mask], z[mask])
		zmap[np.logical_not(mask)] = np.nan
	xyz = np.concatenate((x.flatten()[...,np.newaxis], y.flatten()[...,np.newaxis], z.flatten()[...,np.newaxis]), axis=-1)	
	return (xyz, zmap)


def compose_output_fname(coding_id, n_codes, rec_algo, account_irf=True):
	out_fname = '{}_ncodes-{}_rec-{}'.format(coding_id, n_codes, rec_algo)
	if(account_irf):
		return out_fname + '-irf'
	else:
		return out_fname


if __name__=='__main__':
	
	## Load parameters shared by all
	scan_data_params = load_json('scan_params.json')
	io_dirpaths = load_json('io_dirpaths.json')
	hist_img_base_dirpath = io_dirpaths["preprocessed_hist_data_base_dirpath"]

	## Load processed scene:
	scene_id = '20190209_deer_high_mu/free'
	# scene_id = '20190207_face_scanning_low_mu/free'
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
	hist_img_tau = scan_data_params['hist_preprocessing_params']['hist_end_time'] - scan_data_params['hist_preprocessing_params']['hist_start_time']
	nt = get_nt(hist_img_tau, hist_tbin_size)

	## Load histogram image
	hist_img_fname = get_hist_img_fname(nr, nc, hist_tbin_size, hist_img_tau, is_unimodal=False)
	hist_img_fpath = os.path.join(hist_dirpath, hist_img_fname)
	hist_img = np.load(hist_img_fpath)

	## Shift histogram image if needed
	global_shift = 0
	hist_img = np.roll(hist_img, global_shift, axis=-1)


	denoised_hist_img = gaussian_filter(hist_img, sigma=0.75, mode='wrap', truncate=1)
	(tbins, tbin_edges) = get_hist_bins(hist_img_tau, hist_tbin_size)

	## Load IRF
	irf_tres = scan_data_params['min_tbin_size'] # in picosecs
	irf = get_scene_irf(scene_id, nt, tlen=hist_img_tau, is_unimodal=False)

	## Decode depths
	c_obj = IdentityCoding(hist_img.shape[-1], h_irf=irf, account_irf=True)
	# Get ground truth depths using a denoised histogram image
	matchfilt_tof = c_obj.max_peak_decoding(hist_img, rec_algo_id='matchfilt').squeeze()*hist_tbin_size
	matchfilt_depths = time2depth(matchfilt_tof*1e-12)
	(matchfilt_xyz, matchfilt_zmap) = depths2xyz(time2depth(matchfilt_tof*1e-12), fov_major_axis=scan_data_params['fov_major_axis'], mask=None)

	argmax_tof = hist_img.argmax(axis=-1)*hist_tbin_size
	argmax_depths = time2depth(argmax_tof*1e-12)
	(argmax_xyz, argmax_zmap) = depths2xyz(time2depth(argmax_tof*1e-12), fov_major_axis=scan_data_params['fov_major_axis'], mask=None)

	## estimated signal to background ratio
	nphotons = hist_img.sum(axis=-1)
	bkg_per_bin = np.median(hist_img, axis=-1) 
	signal = np.sum(hist_img - bkg_per_bin[...,np.newaxis], axis=-1)
	signal[signal < 0] = 0
	bkg = bkg_per_bin*nt
	sbr = signal / (bkg + 1e-3)


	plt.clf()
	plt.subplot(2,2,1)
	plt.imshow(matchfilt_tof); plt.title("MatchFilt Depths")
	plt.subplot(2,2,2)
	plt.imshow(argmax_tof); plt.title("Argmax Depths")
	plt.subplot(2,2,3)
	plt.imshow(signal); plt.title("Est. Signal Lvl")
	plt.subplot(2,2,4)
	plt.imshow(bkg); plt.title("Est. Bkg Lvl")