'''
@author: Felipe Gutierrez-Barragan
    Function that loads a histogram and generates the timestamps that created the histogram. 
    The inversion will only be perfect if the input histogram is the same resolution as the timestamps.

    To run simply set the base_dirpath variable below to the correct path, and then run.
'''
## Standard Library Imports
import os

## Library Imports
import numpy as np

## Local Imports

def hist2timestamps(hist_tensor, max_n_timestamps=None):
	'''
		Input:
			* hist_tensor: Tensor whose last dimension is the histogram dimension. Example a tensor with dimsn n_rows x n_cols x n_hist_bins
			* max_n_timestamps: Max number of timestamps that we will accept. If None, then this is derived from the hist with the most timestamps
		Output
			* timestamps_tensor: tensor whose first K-1 dimensions are equal to the hist_tensor. The last dimension depends on max_n_timestamps
	'''
	(hist_tensor, hist_shape) = vectorize_tensor(hist_tensor)
	hist_tensor = hist_tensor.astype(int)
	n_hists = hist_tensor.shape[0]
	n_bins = hist_tensor.shape[-1]
	n_timestamps_per_hist = hist_tensor.sum(axis=-1)
	if(max_n_timestamps is None): max_n_timestamps = np.max(n_timestamps_per_hist)
	timestamp_tensor = -1*np.ones((n_hists, max_n_timestamps)).astype(np.int)
	n_timestamp_per_elem = np.zeros((n_hists,)).astype(np.int)
	for i in range(n_hists):
		curr_hist = hist_tensor[i]
		tmp_timestamp_arr = -1*np.ones((n_timestamps_per_hist[i],))
		curr_idx = 0
		for j in range(n_bins):
			curr_bin_n = curr_hist[j]
			if(curr_bin_n > 0):
				tmp_timestamp_arr[curr_idx:curr_idx+curr_bin_n] = j
				curr_idx = curr_idx+curr_bin_n
		# If number of timestamps is larger than max_n_timestamps, randomly sample max_n
		if(n_timestamps_per_hist[i] >= max_n_timestamps):
			timestamp_tensor[i,:] = np.random.choice(tmp_timestamp_arr, size=(max_n_timestamps,), replace=False)
			n_timestamp_per_elem[i] = max_n_timestamps
		else:
			timestamp_tensor[i,0:n_timestamps_per_hist[i]] = tmp_timestamp_arr
			n_timestamp_per_elem[i] = n_timestamps_per_hist[i]
	return timestamp_tensor.reshape(hist_shape[0:-1] + (max_n_timestamps,)),  n_timestamp_per_elem.reshape(hist_shape[0:-1])

def vectorize_tensor(tensor, axis=-1):
	'''
		Take an N-Dim Tensor and make it a 2D matrix. Leave the first or last dimension untouched, and basically squeeze the 1st-N-1
		dimensions.
		This is useful when applying operations on only the first or last dimension of a tensor. Makes it easier to input to different
		number of pytorch functions.
	'''
	assert((axis==0) or (axis==-1)), 'Error: Input axis needs to be the first or last axis of tensor'
	tensor_shape = tensor.shape
	n_untouched_dim = tensor.shape[axis]
	n_elems = int(round(tensor.size / n_untouched_dim))
	if(axis == -1):
		return (tensor.reshape((n_elems, n_untouched_dim)), tensor_shape)
	else:
		return (tensor.reshape((n_untouched_dim, n_elems)), tensor_shape)

if __name__=='__main__':

    ## Path to raw_hist_imgs folder
    base_dirpath = './data_raw_histograms'

    ## Scene IDs that we can load from
    # scene_id = '20190209_deer_high_mu/free'
    scene_id = '20190207_face_scanning_low_mu/free'
    # scene_id = '20190207_face_scanning_low_mu/ground_truth'

    fname = 'raw-hist-img_r-102-c-58_tres-8ps_tlen-100000ps.npy'

    raw_hist_img = np.load(os.path.join(base_dirpath, scene_id, fname))

    (tstamps_img, n_timestamp_per_elem) = hist2timestamps(raw_hist_img)




    