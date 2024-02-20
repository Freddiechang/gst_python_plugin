# Visual Saliency Guided Foveated Video Compression
A novel video compression method which incorporates the non-uniform spatial resolution of the HVS to reduce perceptual redundancy. The proposed method has the following novel features:
- A foveation process based on per-quad image warping is used to preserve image quality of salient regions, achieving non-uniform subsampling based on saliency level.
- The saliency data is incorporated at a lower granularity, providing more precise quality control of salient regions.
- Our method is independent of traditional encoding processes, making it applicable to improve most existing compression methods.

![Algorithm Overview](/overview.png "Algorithm Overview")
# Setup
- Install GStreamer
- Install GStreamer Plugins
- Configure Gstreamer plugin lib path

See details [here](https://freddiechang.github.io/gstreamer_setup).
# Purge gstreamer plugin cache to reload the python plugin
```
rm -rf ~/.cache/gstreamer-1.0
```
# Citation
```
@ARTICLE{10153607,
  author={Zhang, Shupei and Basu, Anup},
  journal={IEEE Access}, 
  title={Visual Saliency Guided Foveated Video Compression}, 
  year={2023},
  volume={11},
  number={},
  pages={62535-62548},
  keywords={Visualization;Video compression;Redundancy;Spatial resolution;Image quality;Image coding;Transforms;Foveation;perceptual redundancy;video compression;visual saliency},
  doi={10.1109/ACCESS.2023.3286577}}
```
