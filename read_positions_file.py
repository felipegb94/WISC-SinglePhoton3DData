#### Standard Library Imports
import os

#### Library imports
import numpy as np
import matplotlib.pyplot as plt

#### Local imports


POSITIONS_FNAME='positions_file.txt'

def read_positions_file(fpath):
    pos_data = np.genfromtxt(fpath, delimiter=',')
    return pos_data

def get_coords(pos_data):
    (y_pos, x_pos) = (pos_data[:,1], pos_data[:,2])
    (x_coords, x_counts) = np.unique(x_pos, return_counts=True)
    # x_coords[x_counts > 5] = x_coords
    (y_coords, y_counts) = np.unique(y_pos, return_counts=True)
    # y_coords[y_counts > 5] = y_coords
    return (x_coords, y_coords)

if __name__=='__main__':
    base_dirpath = '/home/felipe/datasets/splidar-data-iccv2019/scanDataT3/data'
    ## Scene IDs:
    # 20181108_darkvase, 
    # 20180922_face_no_ambient_highmu, 
    # 20190116_face_scanning_high_mu_no_ambient, 
    # 20190205_face_scanning
    # 20190207_face_scanning_low_mu
    # 20180923_face_mu-0.38_lambda-0.005
    scene_id = '20190207_face_scanning_low_mu/free'
    fname = POSITIONS_FNAME

    # Read file 
    dirpath = os.path.join(base_dirpath, scene_id)
    fpath = os.path.join(dirpath, fname)
    pos_data = read_positions_file(fpath)

    (x_coords, y_coords) = get_coords(pos_data)
    n_rows = y_coords.size
    n_cols = x_coords.size