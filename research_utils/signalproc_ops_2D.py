## Standard Library Imports

## Library Imports
import numpy as np
from scipy import fft
from IPython.core import debugger
breakpoint = debugger.set_trace

## Local Imports
from .shared_constants import *

def dct2(x):
	return fft.dct(fft.dct(x, norm='ortho', axis=-2), norm='ortho', axis=-1)

def idct2(x):
	return fft.idct(fft.idct(x, norm='ortho', axis=-2), norm='ortho', axis=-1)

def generate_dct2d_mat(nr, nc):
	A = np.kron(
		fft.idct(np.identity(nr), norm='ortho', axis=1),
		fft.idct(np.identity(nc), norm='ortho', axis=1) 
		)
	return A.reshape((nr*nc, nr, nc))


