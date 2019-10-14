# Demosaicing Dataset Generator

This repository is a simple implementation of the Demosaicing Dataset Generation algorithm proposed by *Khashabi et al.* on the paper named [*Joint Demosaicing and Denoising via Learned Nonparametric Random Fields*](https://ieeexplore.ieee.org/abstract/document/6906294).

**Disclaimer:** The code presented on this repository was written from scratch (i.e. not using any proprietary code as inspiration or basis). It does, however, require downloading third-party code to access its full features, which is fully credited in this readme file.

## Requirements

- Python 3
- [Dcraw v9](https://www.cybercom.net/~dcoffin/dcraw/)
- Noise estimation code by *Foi et al.* (keep reading to find out more).
- [Matlab Engine for Python R2018a at least](https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)

Note that you'll need a licensed version of Matlab to run the full features of this tool. You can use this tool without it, but you won't be able to estimate noise of images.

## Setup

First, make sure you have a suitable version of Python 3 installed.

### Matlab Python Engine

If you have a version of Matlab installed on your machine, be sure to have Matlab's Python Engine ready to go by following the instructions [here](https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html). If you do not have access to a Matlab distribution or don't want to install it you can keep going, but know that you won't be able to estimate the noise of your input images.

### *Foi et al.*'s Noise Estimation Code

A big part of generating a demosaicing dataset is being capable of replicating the noise of the original image on the subsampled result (read [*Khashabi et al.*](https://ieeexplore.ieee.org/abstract/document/6906294) for more information).

The code capable of estimating the noise of a single channel image is not provided in this repository, for licensing reasons. The code is provided in Matlab P code as an addition to a paper by *Foi et al.* named [*Practical Poissonian-Gaussian Noise Modeling and Fitting for Single-Image Raw-Data*](https://ieeexplore.ieee.org/document/4623175). It can be downloaded [here](http://www.cs.tut.fi/~foi/sensornoise.html). Please note that you'll only need to download the P code used to estimate the noise, which should be only one file.

Place the downloaded code inside the [`noise_estimator`](./noise_estimator) directory. If in dobut, paste all P code files inside that directory, _**without changing their original names**_. The file that this tool will look for is named `function_ClipPoisGaus_stdEst2D.p`, if no file with that name is present on the files you downloaded, try to find out which includes the estimation function and rename it so that it matches the specified name. If you can't get it to work, it might be that the functions have changed substantially, in which case you are welcome to leave an issue, or try to fix it yourself. This project uses version **2.32**, released on June 2015.

## Using the Tool

The best way to use this tool is to clone it on your own machine and follow the setup section. Once that's done, simply execute the main script using python. Assuming you cloned this repository and haven't changed the main directory name, you can simply invoke the tool by issuing the following on a console:

```shell
python demosaicing-dataset-generator
```

Help will be printed explaining how you should invoke the tool to make it work correctly.

## Contributing

Want to contribute? Feel free to leave issues, fork the project and create PRs. Also, we'd love any kind of feedback. You can reach us at <matias.lorenzo@fing.edu.uy> or <gonzalo.balduvino@fing.edu.uy>.
