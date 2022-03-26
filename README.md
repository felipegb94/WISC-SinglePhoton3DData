# WISC-SinglePhoton3DData

Raw single-photon timestamp data processing scripts for data obtained from a Hydrahard TCSPC. The data was captured in an experimental scanning single-photon LiDAR prototype built at UW-Madison by the [Computational Optics](http://compoptics.wisc.edu/) and [WISION](https://wisionlab.cs.wisc.edu/) groups.

## Setup 
### Step 1: Clone repository

```
git clone git@github.com:felipegb94/WISC-SinglePhoton3DData.git
```
### Step 2: Setup Python Environment

The code is tested on Python 3.6. You can setup a conda environment using the `environment.yml` file here or follow these steps:

1. Create environment: `conda create --name SP3DDEnv python=3.6`
2. Activate environment: `conda activate SP3DDEnv`
3. Install packages: `conda install numpy scipy matplotlib ipython gdown`
4. Install `rarfile` needed to unpack the `.rar` data files after download: `pip install rarfile`

### Step 3: Edit Variables in `io_dirpath.json`

Edit  `io_dirpaths.json` file to set the `data_base_dirpath` variable to the directory where you want your data to be downloaded. By default it will download to `./data`.
## Raw Timestamp Data

**Note:** Instead of the raw timestamp data you can download the raw histogram images obtained by loading the timestamps and assembling them into a single 3D histogram image. If you prefer to directly deal with the histogram images skip to the next section

You can download the raw timestamp data using the `download_raw_timestamp_data.py` script. This script only downloads a single scan at a time. Each scan file is between 1-8GB in size. To change the scan that is downloaded edit the `scene_id` variable inside `download_raw_timestamp_data.py`.

For more information about the data folder content that is downloaded for each scan see `README_RawDataInfo.md`.

### Computing Histograms from Raw Timestamp Data

The scripts `read_hydrahard_outfile_t3.py` and `read_fullscan_hydrahard_t3.py`.

1. `read_hydrahard_outfile_t3.py`: Selects a single file from the raw timestamp data and loads it and creates a histogram from it. Each file has the timestamps for a single point in space.
2. `read_fullscan_hydrahard_t3.py`: Reads all the timestamp file for each point in the scan, builds histograms, and reshapes into a 3D histogram image. The output image is saved.

## Raw 3D Histogram Image Data

You can download the raw histogram images using the `download_raw_histogram_data.py` script. This script only downloads a single scan at a time. Each scan file is between 100MB-1GB in size. To change the scan that is downloaded edit the `scene_id` variable inside `download_raw_histogram_data.py`.

### Pre-processing Raw Histograms

The script `preprocess_raw_hist_img.py` preprocesses the raw histograms (crops them and shifts them), and saves them.

The cropping and shift parameters can be set in `scan_params.json`. The shift parameter can be particularly important for pile-up correction on data acquried in synchronous mode.

### Extracting IRF for Depth Estimation

To estimate depths we want to extract the IRF of the system. For each captured scene the alignment of the system may have changed slightly which can change the overall IRF. *Therefore, we extract the IRF for each scene individually from a high SNR point*.

The script `preprocess_per_scene_irf.py` extracts the scene IRF and saves it. 

**Important Note:** For data acquired in synchronous mode, i.e., that has pile-up, you may need to perform pile-up correction before extracting the IRF.

### Estimating depths

There are two simple methods to estimate depths from the pre-processed histograms:

1. *Argmax*: Take the argmax across the time dimension
1. *matchfilt*: Use the previously extracted IRF and estimate depths using matched filtering. The script `process_hist_img.py` shows an example of how this can be done. Note that before running this script for a given scene you need to have ran `preprocess_raw_hist_img.py` and also `preprocess_per_scene_irf.py` for the given scene.

## Code and Scripts

Here are descriptions for the code files provided:

* `read_hydraharp_outfile_t3.py`: Contains functions to read the raw timestamp data. The main function simply reads a single timestamps file, builds a histogram and displays it.
* `pileup_correction`: Pile-up correction algorithms for timestamp data obtained in synchronous and in free running mode. The free running mode does not change the histograms too much. For the synchronous mode you need to make sure that the histogram is correctly shifted (0th time bin is actually the early time bins).
* `scan_data_utils.py` and `research_utils/`: Some utility functions used by the scripts here.


## Citation and Reference

The code and data in this repository comes from 3 different projects.

* Initial Code + Data for Optimal attenuation results:

```latex
@inproceedings{gupta2019photon,
  title={Photon-flooded single-photon 3D cameras},
  author={Gupta, Anant and Ingle, Atul and Velten, Andreas and Gupta, Mohit},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  pages={6770--6779},
  year={2019}
}
```

* Initial Code + Data for asynchronous acquisition results:

```latex
@inproceedings{gupta2019asynchronous,
  title={Asynchronous single-photon 3D imaging},
  author={Gupta, Anant and Ingle, Atul and Gupta, Mohit},
  booktitle={Proceedings of the IEEE/CVF International Conference on Computer Vision},
  pages={7909--7918},
  year={2019}
}
```

* Current version of the code was implemented for:

```latex
@inproceedings{gutierrez2022compressive,
  title={Compressive Single-Photon 3D Cameras},
  author={Gutierrez-Barragan, Felipe and Ingle, Atul and Seets, Trevor and Gupta, Mohit and Velten, Andreas},
  booktitle={Proceedings of the IEEE/CVF International Conference on Computer Vision},
  year={2022}
}
```
