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
## Downloading the Data

You can download the data using the `download_data.py` script. This script only downloads a single scan at a time. Each scan file is between 1-8GB in size.

To change the scan that is downloaded edit the `scene_id` variable inside `download_data.py`.

For more information about the data folder content that is downloaded for each scan see `README_RawDataInfo.md`.

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
