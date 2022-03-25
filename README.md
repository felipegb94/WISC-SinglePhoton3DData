# WISC-SinglePhoton3DData

Raw single-photon timestamp data processing scripts for data obtained from a Hydrahard TCSPC. The data was captured in an experimental scanning single-photon LiDAR prototype built at UW-Madison by the [Computational Optics](http://compoptics.wisc.edu/) and [WISION](https://wisionlab.cs.wisc.edu/) groups.

## Setup 

Begin by cloning this repository recursively to include the submodules:

```
git clone git@github.com:felipegb94/WISC-SinglePhoton3DData.git
```


### Python Environment

The code is tested on Python 3.6. You can setup a conda environment using the `environment.yml` file here or follow these steps:

1. Create environment: `conda create --name SP3DDEnv python=3.6`
2. Install packages: `conda install numpy scipy matplotlib ipython gdown`

## Download data scripts

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
