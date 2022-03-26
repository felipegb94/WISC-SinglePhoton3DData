'''
	Base class for temporal coding schemes
'''
## Standard Library Imports
from abc import ABC, abstractmethod

## Library Imports
import numpy as np
from scipy import signal, interpolate
from scipy.special import softmax
from IPython.core import debugger
breakpoint = debugger.set_trace

## Local Imports
from research_utils.shared_constants import *
from research_utils import signalproc_ops, np_utils, py_utils


def norm_t(C, axis=-1):
	'''
		Divide by standard deviation across given axis
	'''
	return C / (np.linalg.norm(C, ord=2, axis=axis, keepdims=True) + EPSILON)

def zero_norm_t(C, axis=-1):
	'''
		Apply zero norm transform to give axis
		This performs exactly the same as the old zero_norm_t_old, but in the old version denominator is scale by a factor of (1/sqrt(K)) which is part of the standard deviation formula
	'''
	return norm_t(C - C.mean(axis=axis, keepdims=True), axis=axis)

class Coding(ABC):
	'''
		Abstract class for linear coding
	'''
	C = None
	h_irf = None
	def __init__(self, h_irf=None, account_irf=False):
		# Set the coding matrix C if it has not been set yet
		if(self.C is None): self.set_coding_mat()
		# 
		(self.n_maxres, self.n_codes) = (self.C.shape[-2], self.C.shape[-1])
		# Set the impulse response function (used for accounting for system band-limit and match filter reconstruction)
		self.update_irf(h_irf)
		# the account_irf flag controls if we want to account IRF when estimating shifts. 
		# This means that the C matrices used during decoding may be different from the encoding one
		self.account_irf = account_irf
		# Update all the parameters derived from C
		self.update_C_derived_params()
		# Get all functions for reconstruction and decoding available
		self.rec_algos_avail = py_utils.get_obj_functions(self, filter_str='reconstruction')
		# Set if we want to account for IRF when decoding

	@abstractmethod
	def set_coding_mat(self):
		'''
		This method initializes the coding matrix, self.C
		'''
		pass

	def update_irf(self, h_irf=None):
		# If nothing is given set to gaussian
		if(h_irf is None): 
			print("hirf is NONE")
			self.h_irf = np.zeros((self.n_maxres,))
			self.h_irf[0] = 1.
		else: self.h_irf = h_irf.squeeze()
		assert(self.h_irf.ndim == 1), "irf should be 1 dim vector"
		assert(self.h_irf.shape[-1] == self.n_maxres), "irf size should match n_maxres"
		assert(np.all(self.h_irf >= 0.)), "irf should be non-negative"
		# normalize
		self.h_irf = self.h_irf / self.h_irf.sum() 

	def update_C(self, C=None):
		if(not (C is None)): self.C = C
		# update any C derived params
		self.update_C_derived_params()
	
	def update_C_derived_params(self):
		# Store how many codes there are
		(self.n_maxres, self.n_codes) = (self.C.shape[-2], self.C.shape[-1])
		assert(self.n_codes <= self.n_maxres), "n_codes ({}) should not be larger than n_maxres ({})".format(self.n_codes, self.n_maxres)
		if(self.account_irf):
			# self.decoding_C = signalproc_ops.circular_conv(self.C, self.h_irf[:, np.newaxis], axis=0)
			# self.decoding_C = signalproc_ops.circular_corr(self.C, self.h_irf[:, np.newaxis], axis=0)
			self.decoding_C = signalproc_ops.circular_corr(self.h_irf[:, np.newaxis], self.C, axis=0)
		else:
			self.decoding_C = self.C
		# Pre-initialize some useful variables
		self.zero_norm_C = zero_norm_t(self.decoding_C)
		self.norm_C = norm_t(self.decoding_C)
		# Set domains
		self.domain = np.arange(0, self.n_maxres)*(TWOPI / self.n_maxres)

	def get_n_maxres(self): return self.n_maxres

	def get_domain(self): return self.domain

	def get_input_C(self, input_C=None):
		if(input_C is None): input_C = self.C
		self.verify_input_c_vec(input_C) # Last dim should be the codes
		return input_C

	def get_input_zn_C(self, zn_input_C=None):
		if(zn_input_C is None): zn_input_C = self.zero_norm_C
		self.verify_input_c_vec(zn_input_C) # Last dim should be the codes
		return zn_input_C
		
	def get_input_norm_C(self, norm_input_C=None):
		if(norm_input_C is None): norm_input_C = self.norm_C
		self.verify_input_c_vec(norm_input_C) # Last dim should be the codes
		return norm_input_C

	def encode(self, transient_img):
		'''
		Encode the transient image using the n_codes inside the self.C matrix
		'''
		assert(transient_img.shape[-1] == self.n_maxres), "Input c_vec does not have the correct dimensions"
		return np.matmul(transient_img[..., np.newaxis, :], self.C).squeeze(-2)

	def verify_input_c_vec(self, c_vec):
		assert(c_vec.shape[-1] == self.n_codes), "Input c_vec does not have the correct dimensions"

	def get_rec_algo_func(self, rec_algo_id):
		# Check if rec algorithm exists
		rec_algo_func_name = '{}_reconstruction'.format(rec_algo_id)
		rec_algo_function = getattr(self, rec_algo_func_name, None)
		assert(rec_algo_function is not None), "Reconstruction algorithm {} is NOT available. Please choose from the following algos: {}".format(rec_algo_func_name, self.rec_algos_avail)
		# # Apply rec algo
		# print("Running reconstruction algorithm {}".format(rec_algo_func_name))
		return rec_algo_function
	
	def reconstruction(self, c_vec, rec_algo_id='linear', **kwargs):
		rec_algo_function = self.get_rec_algo_func(rec_algo_id)
		lookup = rec_algo_function(c_vec, **kwargs)
		return lookup

	def max_peak_decoding(self, c_vec, rec_algo_id='linear', **kwargs):
		'''
			Perform max peak decoding using the specified reconstruction algorithm
			kwargs (key-work arguments) will depend on the chosen reconstruction algorithm 
		'''
		lookup = self.reconstruction(c_vec, rec_algo_id, **kwargs)
		return np.argmax(lookup, axis=-1)

	def maxgauss_peak_decoding(self, c_vec, gauss_sigma, rec_algo_id='linear', **kwargs):
		lookup = self.reconstruction(c_vec, rec_algo_id, **kwargs)
		return signalproc_ops.max_gaussian_center_of_mass_mle(lookup, sigma_tbins = gauss_sigma)



class GatedCoding(Coding):
	'''
		Gated coding class. Coding is applied like a gated camera 
		In the extreme case that we have a gate for every time bin then the C matrix is an (n_maxres x n_maxres) identity matrix
	'''
	def __init__(self, n_maxres, n_gates=None, **kwargs):
		if(n_gates is None): n_gates = n_maxres
		assert((n_maxres % n_gates) == 0), "Right now GatedCoding required n_maxres to be divisible by n_gates"
		assert((n_maxres >= n_gates)), "n_gates should always be smaller than n_maxres"
		self.n_gates = n_gates
		self.set_coding_mat(n_maxres, n_gates)
		super().__init__(**kwargs)

	def set_coding_mat(self, n_maxres, n_gates):
		self.gate_len = int(n_maxres / n_gates)
		self.C = np.zeros((n_maxres, n_gates))
		for i in range(n_gates):
			start_tbin = i*self.gate_len
			end_tbin = start_tbin + self.gate_len
			self.C[start_tbin:end_tbin, i] = 1.
	
	def encode(self, transient_img):
		'''
		Encode the transient image using the n_codes inside the self.C matrix
		For GatedCoding with many n_gates, encoding through matmul is quite slow, so we assign it differently
		'''
		assert(transient_img.shape[-1] == self.n_maxres), "Input c_vec does not have the correct dimensions"
		c_vals = np.array(transient_img[..., 0::self.gate_len])
		for i in range(self.gate_len-1):
			start_idx = i+1
			c_vals += transient_img[..., start_idx::self.gate_len]
		return c_vals

	def linear_reconstruction(self, c_vals):
		if(self.n_gates == self.n_maxres): return c_vals
		if(self.account_irf):
			print("Warning: Linear Reconstruction in Gated does not account for IRF, so unless the IRF spreads across time bins, this will produce quantized depths")
		x_fullres = np.arange(0, self.n_maxres)
		# Create a circular x axis by concatenating the first element to the end and the last element to the begining
		circular_x_lres = np.arange((0.5*self.gate_len)-0.5-self.gate_len, self.n_maxres + self.gate_len, self.gate_len)
		circular_c_vals = np.concatenate((c_vals[..., -1][...,np.newaxis], c_vals, c_vals[..., 0][...,np.newaxis]), axis=-1)
		f = interpolate.interp1d(circular_x_lres, circular_c_vals, axis=-1, kind='linear')
		return f(x_fullres)
	
	def matchfilt_reconstruction(self, c_vals):
		template = self.h_irf
		self.verify_input_c_vec(c_vals)
		zn_template = zero_norm_t(template, axis=-1)
		zn_c_vals = zero_norm_t(c_vals, axis=-1)
		shifts = signalproc_ops.circular_matched_filter(zn_c_vals, zn_template)
		# vectorize tensors
		(c_vals, c_vals_shape) = np_utils.vectorize_tensor(c_vals, axis=-1)
		shifts = shifts.reshape((c_vals.shape[0],))
		h_rec = np.zeros(c_vals.shape, dtype=template.dtype)
		for i in range(shifts.size): h_rec[i,:] = np.roll(template, shift=shifts[i], axis=-1)
		c_vals = c_vals.reshape(c_vals_shape)
		return h_rec.reshape(c_vals_shape)

class IdentityCoding(GatedCoding):
	'''
		Identity coding class. GatedCoding in the extreme case where n_maxres == n_gates
	'''
	def __init__(self, n_maxres, **kwargs):
		super().__init__(n_maxres=n_maxres, **kwargs)