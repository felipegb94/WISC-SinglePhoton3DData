## Standard Library Imports
import sys
sys.path.append('../')

## Library Imports
import numpy as np
import matplotlib.pyplot as plt
from scipy import fft
from IPython.core import debugger
breakpoint = debugger.set_trace

## Local Imports
from research_utils.signalproc_ops_2D import *
from research_utils.shared_constants import *


def test_dct2_idct2_invertibility(img):
	## Test dct2 and idct2
	dct2_img = dct2(img)
	rec_img = idct2(dct2_img)
	assert(np.allclose(img, rec_img, atol=EPSILON)), "dct2 and idct2 do not reverse the operation"
	print("PASSED test_dct2_idct2_invertibility")

def test_dct2mat(img):
	dct2_img1 = dct2(img)
	(nr,nc) = img.shape
	dct2mat = generate_dct2d_mat(nr, nc)
	dct2_img2 = np.zeros((nr*nc,))
	for i in range(nr*nc):
		dct2_img2[i] = np.sum(np.multiply(dct2mat[i,:], img))
	dct2_img2 = dct2_img2.reshape((nr,nc))
	assert(np.allclose(dct2_img1, dct2_img2, atol=EPSILON)), "dct2 and idct2 do not reverse the operation"
	print("PASSED test_dct2mat")

if __name__=='__main__':
	from skimage import data
	from skimage.transform import resize

	## Load sample image data and resize
	img = data.coins()
	img = resize(img, (img.shape[0]//4,img.shape[1]//4))

	## Test
	test_dct2_idct2_invertibility(img)
	test_dct2_idct2_invertibility(np.random.rand(20,20))

	## Test dct2 matrix
	test_dct2mat(img)
	test_dct2mat(np.random.rand(20,20))
	test_dct2mat(np.random.rand(23,18))
	test_dct2mat(np.random.rand(13,40))
