# -*- coding: utf-8 -*-
"""
Created on Thu Dec 21 10:26:46 2017

@author: compoptics, modified by felipe 08-26-2021
"""
#### Standard Library Imports
import os
import struct
import sys
sys.path.append('./tof-lib')

#### Library imports
import numpy as np
import matplotlib.pyplot as plt
from IPython.core import debugger
breakpoint = debugger.set_trace

#### Local imports
from scan_data_scripts.scan_data_utils import *
from scan_data_scripts.pileup_correction import *
from research_utils.plot_utils import *
from research_utils.timer import Timer
from research_utils.io_ops import load_json

DEBUG = False

def got_photon(time_tag, channel, dtime):
	print('CHN',channel,'time_tag',time_tag,'dtime',dtime)

def got_overflow(count):
	print('OFL *',count)

def read_hydraharp_outfile_t3(outfilename):
	"""Function to read .out files (headerless) saved using tttr-t3.exe binary executable.
	Input:
		.out filename with full path
	Outputs:
		sync_vec is an array of sync pulse number which just counts up sequentially. A
		missing number means no photons were received for that cycle. If you
		know the rep rate of your laser, you can compute the time difference between
		consecutive sync pulses by taking the difference between their indexes and multiplying
		by the rep interval.
		
		dtime_vec is an array of 15-bit integer values (between 0 and 32767) that
		gives the time of arrival of the first photon with respect to its corresponding
		sync pulse number in the sync_vec array.
		You can convert dtime_vec to picoseconds using the bin resolution that was set during
		data acquisition on the TCSPC. (Default 8ps). 
		eg.: if sync_vec[10] = 42 and dtime_vec[10]=325 it means the photon was recorded
		after 325x8ps after the 42nd sync pulse. Also note that since the 10^th index of
		the vector corresponds to the 42nd sync pulse, it means many of the initial pulses
		did not record any returning photons, so their sync pulse numbers were missing.
		
		To avoid a truncated time response, you need to ensure that
		laser rep time interval <= (TCSPC bin resolution) x 32767
	"""
	T3WRAPAROUND = 1024
	BYTES_PER_RECORD = 4
	f = open(outfilename,"rb")
	f.seek(0,2)
	ftell = f.tell()
	# cast to int, even though ftell and BYTES_PER_RECORD are int, the division casts them to float 
	num_recs = int(ftell/BYTES_PER_RECORD)
	f.seek(0)

	dtime_vec = np.zeros(num_recs, dtype=np.int32)
	sync_vec = np.zeros(num_recs, dtype=np.int32)
	
	ndrecs = 0

	overflow_correction= 0
	num_photons = 0
	num_overflow = 0
	
	for _ in range(num_recs):
		bytstr = f.read(4)
		if bytstr=='':
			print('file corrupt. wrong num of recs')
			break
		
		buf0 = struct.unpack('I',bytstr)[0]
		nsync   =  buf0 & 0b00000000000000000000001111111111
		dtime   = (buf0 & 0b00000001111111111111110000000000)>>10
		channel = (buf0 & 0b01111110000000000000000000000000)>>25
		special = buf0 >> 31

		if not special:
			true_nsync = overflow_correction + nsync;
			sync_vec[ndrecs] = true_nsync
			dtime_vec[ndrecs] = dtime
			ndrecs+=1
			if DEBUG:
				got_photon(true_nsync, channel, dtime)
			num_photons+=1 #got a photon
		else: 
			# special record - could be overflow or marker
			if channel==63:
				if nsync==0:
					overflow_correction += T3WRAPAROUND
					num_overflow+=1
					if DEBUG:
						got_overflow(1)
				else:
					overflow_correction += T3WRAPAROUND*nsync
					num_overflow+=nsync
					if DEBUG:
						got_overflow(nsync)
			if channel>=1 and channel<=15:
				print('marker received. something wrong with cables?')

	f.close()
	return (sync_vec[0:ndrecs],dtime_vec[0:ndrecs])


def read_hydraharp_outfile_t3_with_gate(outfilename):
	"""Function to read .out files (headerless) saved using tttr-t3.exe binary executable.
	Input:
		.out filename with full path
	Outputs:
		sync_vec is an array of sync pulse number which just counts up sequentially. A
		missing number means no photons were received for that cycle. If you
		know the rep rate of your laser, you can compute the time difference between
		consecutive sync pulses by taking the difference between their indexes and multiplying
		by the rep interval.
		
		dtime_vec is an array of 15-bit integer values (between 0 and 32767) that
		gives the time of arrival of the first photon with respect to its corresponding
		sync pulse number in the sync_vec array.
		You can convert dtime_vec to picoseconds using the bin resolution that was set during
		data acquisition on the TCSPC. (Default 8ps). 
		eg.: if sync_vec[10] = 42 and dtime_vec[10]=325 it means the photon was recorded
		after 325x8ps after the 42nd sync pulse. Also note that since the 10^th index of
		the vector corresponds to the 42nd sync pulse, it means many of the initial pulses
		did not record any returning photons, so their sync pulse numbers were missing.
		
		To avoid a truncated time response, you need to ensure that
		laser rep time interval <= (TCSPC bin resolution) x 32767
	"""
	T3WRAPAROUND = 1024
	BYTES_PER_RECORD = 4
	f = open(outfilename,"rb")
	f.seek(0,2)
	ftell = f.tell()
	# cast to int, even though ftell and BYTES_PER_RECORD are int, the division casts them to float 
	num_recs = int(ftell/BYTES_PER_RECORD)
	f.seek(0)
	
	dtime_vec = np.zeros(num_recs, dtype=np.int32)
	sync_vec = np.zeros(num_recs, dtype=np.int32)
	
	dtime_vec_gate = np.zeros(num_recs, dtype=np.int32)
	sync_vec_gate = np.zeros(num_recs, dtype=np.int32)
	
	ndrecs = 0
	ndrecs_gate = 0
	
	overflow_correction= 0
	num_photons = 0
	num_overflow = 0
	
	for _ in range(num_recs):
		bytstr = f.read(4)
		if bytstr=='':
			print('file corrupt. wrong num of recs')
			break
		
		buf0 = struct.unpack('I',bytstr)[0]
		nsync   =  buf0 & 0b00000000000000000000001111111111
		dtime   = (buf0 & 0b00000001111111111111110000000000)>>10
		channel = (buf0 & 0b01111110000000000000000000000000)>>25
		special = buf0 >> 31

		if not special:
			true_nsync = overflow_correction + nsync;
			if channel==0:
				sync_vec[ndrecs] = true_nsync
				dtime_vec[ndrecs] = dtime
				ndrecs+=1
			elif channel==1:
				sync_vec_gate[ndrecs_gate] = true_nsync
				dtime_vec_gate[ndrecs_gate] = dtime
				ndrecs_gate+=1
			if DEBUG:
				got_photon(true_nsync, channel, dtime)
			if channel==0:
				num_photons+=1 #got a photon
		else: 
			# special record - could be overflow or marker
			if channel==63:
				if nsync==0:
					overflow_correction += T3WRAPAROUND
					num_overflow+=1
					if DEBUG:
						got_overflow(1)
				else:
					overflow_correction += T3WRAPAROUND*nsync
					num_overflow+=nsync
					if DEBUG:
						got_overflow(nsync)
			if channel>=1 and channel<=15:
				print('marker received. something wrong with cables?')

	f.close()
	return (sync_vec[0:ndrecs],dtime_vec[0:ndrecs],sync_vec_gate[0:ndrecs_gate],dtime_vec_gate[0:ndrecs_gate])

def parse_scan_pos_idx(fname): return int(fname.split('.')[-2].split('_')[-1])

def parse_is_long_cable_flag(fname): return int(fname.split('.')[-2].split('_')[1])

def parse_delay_param(fname): return int(fname.split('.')[-2].split('_')[2])

def count_params_in_fname(fname): return len(fname.split('.')[-2].split('_'))-1

def calc_hist_shift(fname, hist_tbin_size):
	'''Function to calc shift histogram to account for time delays in system due to cables and scan time
	'''
	start_bin = 32408+2224
	end_bin = start_bin + 84096
	# delay = int(fname.split('.')[0].split('_')[-1]) # delay due to scan time?
	delay = parse_delay_param(fname) # delay due to scan time?
	is_long_cable = parse_is_long_cable_flag(fname)
	cable_delay = is_long_cable * 81624 + (1 - is_long_cable) * 36864
	delay += cable_delay
	roll_amount = -(-81624 - 48384 + delay + start_bin)
	# roll_amount /= 8
	roll_amount /= hist_tbin_size # calc number of elements to shift
	# print((cable_delay + 48384 - delay + start_bin))
	return roll_amount

if __name__=='__main__':
	## Load parameters shared by all
	scan_data_params = load_json('scan_data_scripts/scan_params.json')
	
	base_dirpath = scan_data_params['scan_data_base_dirpath']
	## Scene IDs:
	scene_id = '20190207_face_scanning_low_mu/free'
	fname = 't3mode_0_000000_10295.out' # Nose
	fname = 't3mode_0_000000_14467.out' # Background
	# fname = 't3mode_0_000000_19723.out' # Upper rgiht cheeck
	# fname = 't3mode_0_000000_21345.out' # Right ear
	# scene_id = '20190207_face_scanning_low_mu/ground_truth'
	# fname = 't3mode_0_000000_10295.out' # Nose
	# fname = 't3mode_0_000000_14467.out' # Background
	# fname = 't3mode_0_000000_19723.out' # Upper rgiht cheeck
	# fname = 't3mode_0_000000_21345.out' # Right ear
	# scene_id = '20190205_face_scanning/free'
	# fname = 't3mode_0_000000_5757.out'
	# fname = 't3mode_0_000000_1757.out'
	# scene_id = '20190205_face_scanning/ext_opt_filtering'
	# fname = 't3mode_0_000000_5757.out'

	# Read file 
	dirpath = os.path.join(base_dirpath, scene_id)
	fpath = os.path.join(dirpath, fname)

	# fname = 'E:/scanDataT3/data/t3mode_1_048484.out'
	sync_vec, dtime_vec = read_hydraharp_outfile_t3(fpath)

	# discard timestamps to make things faster
	max_n_tstamps = int(1e8)
	abs_max_n_tstamps = dtime_vec.size
	max_n_tstamps = np.min([max_n_tstamps, dtime_vec.size])
	(dtime_vec, sync_vec) = (dtime_vec[0:max_n_tstamps], sync_vec[0:max_n_tstamps]) 

	# Calc Parameters for Coates Estimator
	n_laser_cycles = sync_vec.max()
	n_empty_laser_cycles = calc_n_empty_laser_cycles(sync_vec)
	laser_rep_freq = scan_data_params['laser_rep_freq'] # most data acquisitions were done with a 10MHz laser rep freq
	laser_rep_period = (1. / laser_rep_freq)*1e12 # In picosecs
	total_acquisition_time = n_laser_cycles*laser_rep_period # in picosecs

	## Create histogram
	# max_tbin / min_tbnin_size determin the length of the histogram
	# If there are timestamps larger than max_tbin the will be discarded when building the histogram 
	max_tbin = laser_rep_period # Period in ps
	min_tbin_size = scan_data_params['min_tbin_size'] # Bin size in ps
	hist_tbin_factor = 1.0 # increase tbin size to make histogramming faster
	hist_tbin_size = min_tbin_size*hist_tbin_factor # increase size of time bin to make histogramming faster
	(counts, bin_edges, bins) = timestamps2histogram(dtime_vec, max_tbin=max_tbin, min_tbin_size=min_tbin_size, hist_tbin_factor=hist_tbin_factor)
	n_hist_bins = counts.size
	# if('calib' in fname): roll_amount = 0
	# else: roll_amount = calc_hist_shift(fname, hist_tbin_size)
	roll_amount=0
	counts = np.roll(counts, int(roll_amount))

	## Verify that the number of laser cycles still matches n_laser_cycles gotten from sync_vec
	n_laser_cycles_validate = np.round(total_acquisition_time / (n_hist_bins*hist_tbin_size))
	if(n_laser_cycles != n_laser_cycles_validate): print("WARNING: n_laser_cycles do not match calculated..")
	## correct histogram (Coates estimate)
	dead_time = scan_data_params['dead_time'] # dead time in picoseconds
	if('free' in scene_id):
		corrected_counts = coates_est_free_running(counts, laser_rep_period, hist_tbin_size, dead_time)
	elif(('ground_truth' in scene_id) or ('ext' in scene_id)):
		corrected_counts = coates_correction_sync_mode(counts, n_laser_cycles)
	else:
		corrected_counts = counts
	# some useful calcs
	max_n_photons_per_cycle = int(np.ceil(max_tbin / dead_time))
	dead_time_bins = int(np.floor(dead_time / hist_tbin_size))
	# Max number of photons that a bin can have detected. This is equal to # of laser cycles. If we downsampled histogram then it will be n_laser_cycles*hist_tbin_factor
	max_photons_per_bin = int(n_laser_cycles * hist_tbin_factor)*max_n_photons_per_cycle

	print("Hist Params:")
	print("   - n_bins = {}".format(bins.shape))
	print("   - n_counts = {}".format(counts.sum()))
	print("   - n_timestamps_used = {}".format(dtime_vec.shape))
	print("   - n_timestamps_avail = {}".format(abs_max_n_tstamps))
	print("   - MIN timestamp in file = {}".format(min_tbin_size*np.min(dtime_vec)))
	print("   - MAX timestamp in file = {}".format(min_tbin_size*np.max(dtime_vec)))
	
	# Check if all laser pulses counter are unique
	# If all the pulses are unique, it usually means that we were operated in synchronous mode (ext triggering with laser).
	u, c = np.unique(sync_vec, return_counts=True)
	dup = u[c>1]
	if(dup.size > 0): print('    - sync_vec HAS duplicate entries')
	else: print('   - sync_vec DOES NOT HAVE duplicate entries')

	results_dirpath = load_json('io_dirpaths.json')['results_dirpath']
	results_dirpath = os.path.join(results_dirpath, 'real_data_results/per_pixel')

	# Plot
	# plt.clf()
	plt.plot(bins, counts / n_laser_cycles, alpha=0.75, label='Uncorrected: '+fname)
	plt.plot(bins, corrected_counts, alpha=0.75, label='Corrected: '+fname)
	# plt.plot(bins, counts , alpha=0.75, label=fname)
	plt.legend(fontsize=16)
	plt.xlim([0,max_tbin])
	plt.pause(0.1)
	out_fname = '{}_{}'.format(scene_id.replace('/','--'),fname.replace('.out',''))
	save_currfig_png(results_dirpath, out_fname)
	plt.pause(0.1)

	# plt.xlim([34500,47000])
	# out_fname = '{}_{}_zoom1'.format(scene_id.replace('/','--'),fname.replace('.out',''))
	# save_currfig_png(results_dirpath, out_fname)

	# plt.xlim([58000,80000])
	# out_fname = '{}_{}_zoom2'.format(scene_id.replace('/','--'),fname.replace('.out',''))
	# save_currfig_png(results_dirpath, out_fname)

	# plt.xlim([0,max_tbin])
	# plt.ylim([0,0.0008])
	# out_fname = '{}_{}_zoom3'.format(scene_id.replace('/','--'),fname.replace('.out',''))
	# save_currfig_png(results_dirpath, out_fname)

