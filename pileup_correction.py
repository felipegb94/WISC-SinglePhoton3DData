#### Standard Library Imports

#### Library imports
import numpy as np
import matplotlib.pyplot as plt
from IPython.core import debugger
breakpoint = debugger.set_trace

#### Local imports
from scan_data_utils import *


def coates_correction_sync_mode(counts, n_laser_cycles):
	'''
		Coates correction described in Eq. 6 of Gupta et al., CVPR 2019
		- counts: Histogram of timestamps
		- n_empty_laser_cycles: Number of laser cycles with no photons
		- n_laser_cycles: total number of laser cycles
		NOTE: Although numer/denom calc could be vectorized, it does not speed up. 
		Using for loop is faster than using linear algebra in this case
	'''
	print("WARNING: For coates correction to work, the input histogram needs to be correctly shifted such that the 0th time bin actually corresponds to the earlier time bins. ")
	assert(counts.ndim==1), 'only implemented for single histogram at a time'
	B = counts.shape[-1] # number of bins
	N_i = np.array(counts, dtype=np.float32) # histogram with one additional bin
	r_i_hat = np.zeros((B,), dtype=N_i.dtype)
	for i in range(B):
		numer = n_laser_cycles - np.sum(N_i[0:i])
		denom = numer - N_i[i]
		if denom<1e-15: continue
		r_i_hat[i] = np.log(numer/denom)
	return r_i_hat

def coates_correction_sync_mode_fullimg(counts, n_laser_cycles):
	'''
		Coates correction described in Eq. 6 of Gupta et al., CVPR 2019
		- counts: Image or list of histograms. Last dimension should be the histogram dimension. First N dimensions will be for the list/image of histograms
		- n_empty_laser_cycles: Number of laser cycles with no photons
		- n_laser_cycles: total number of laser cycles
	'''
	print("WARNING: For coates correction to work, the input histogram needs to be correctly shifted such that the 0th time bin actually corresponds to the earlier time bins. ")
	B = counts.shape[-1] # number of bins
	N_i = np.array(counts, dtype=np.float32) # histogram with one additional bin
	r_i_hat = np.zeros_like(N_i)
	for i in range(B):
		numer = n_laser_cycles - N_i[..., 0:i].sum(axis=-1)
		denom = numer - N_i[..., i]
		# if denom<1e-15: continue
		nonzero_mask = denom > 1e-15
		curr_r_i_hat = r_i_hat[..., i]
		curr_r_i_hat[nonzero_mask] = np.log(numer[nonzero_mask]/denom[nonzero_mask]) 
		# r_i_hat[..., i] = np.log(numer[nonzero_mask]/denom[nonzero_mask])
	return r_i_hat

def coates_est_free_running(counts, rep_period, hist_tbin_size, dead_time, n_laser_cycles, hist_tbin_factor=1):
	'''
		Coates correction as described in Suppl. Note 5
		- counts: Histogram of timestamps
		- rep_period: laser repetition period
		- hist_tbin_size: size of histogram time bin
		- dead_time: spad dead time
		- n_laser_cycles: number of laser cycles
		- hist_tbin_factor: 1 if histogram bin size == time resolution. > 1 if we downsampled the histogram
		NOTE: The units of rep_period, hist_tbin_size, and dead_time should match 
		NOTE: Usually the correction does not change the shape of free running too much
	'''
	assert(counts.ndim==1), 'only implemented for single histogram at a time'
	## correct histogram (Coates estimate)
	max_n_photons_per_cycle = int(np.ceil(rep_period / dead_time))
	dead_time_bins = int(np.floor(dead_time / hist_tbin_size))
	# Max number of photons that a bin can have detected. This is equal to # of laser cycles. If we downsampled histogram then it will be n_laser_cycles*hist_tbin_factor
	max_photons_per_bin = int(n_laser_cycles * hist_tbin_factor)*max_n_photons_per_cycle
	# init the denominator seq to the max number of photons that could have been detected by a bin
	denominator_seq = np.ones_like(counts) * max_photons_per_bin
	n_hist_bins = counts.shape[-1]
	assert(counts.ndim==1), 'only implemented for single histogram at a time'
	for i in range(n_hist_bins):
		start_bin = i + 1
		end_bin = np.min([start_bin + dead_time_bins, n_hist_bins])
		# Wrapped bin always start at 0
		wrapped_start_bin = 0
		# If there is no wrapping (start_bin + dead_time_bins - n_hist_bins < 0) so wrapped_end_bin is 0        
		wrapped_end_bin = np.max([0, start_bin + dead_time_bins - n_hist_bins])
		n_bins = (end_bin - start_bin) + (wrapped_end_bin - wrapped_start_bin)
		# print("n_bins: {}, start: {}, end: {}, wrapped_start: {}, wrapped_end: {}".format(n_bins, start_bin, end_bin, wrapped_start_bin, wrapped_end_bin))
		assert(n_bins == dead_time_bins), "Coates correction bins should always be equal to the number of dead time bins"
		curr_bin_counts = counts[i]
		denominator_seq[start_bin:end_bin] -= curr_bin_counts
		denominator_seq[wrapped_start_bin:wrapped_end_bin] -= curr_bin_counts

	corrected_counts = counts / denominator_seq
	return corrected_counts