# Information about raw data downloaded

Each data folder downloaded will have one or more folders in it that describe the operating mode or amount of filtering used to mitigate pile-up.

The folder naming convention is as follow:

* `free`: Free running mode == Photon-driven mode, as decribed in Gupta et al., ICCV 2019
* `det`: Deterministic shifting == Uniform shifting mode, as decribed in Gupta et al., ICCV 2019
* `ext`: External triggering (by laser). Synchronous mode. No attenuation
* `ext_opt_filtering`: External triggering (by laser). Synchronous mode. Optimal Filterning
* `pulse_waveform_calib`: Single point scan for calibrating waveform. Some waveforms still had undesired reflections.

## Scan Data Scene IDs

There are scans from Gupta et al., CVPR 2019 and from Gupta et al., ICCV 2019. As you will obsserve in the `download_data.py` script you can specify the `scene_id` you want to download. Here we list all the scene ids you can select, and from which paper those scenes correspond to. 

### Raw data from scans from Gupta et al., CVPR 2019

* `20190207_face_scanning_low_mu`: Scan of a manequin face with a flat wall background.
* `20190209_deer_high_mu`: Scan of a reindeer wooden structure.

### Raw data from scans from Gupta et al., ICCV 2019