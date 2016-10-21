# PySpectro Release Notes

##Version 1.1

###Description

* Added several new code demonsrations for programattically 
   interacting with the spectrometer driver and the core application.
* Demonsration of recordig data in HDS5 format, and reading it 
   back to plot a spectrogram in either Python or Matlab.
* Added a demonsration script to generate the FFT memory indices
* Removed bitfiles that are now automatically handled by the installer
* Log files are now placed in the user's home directory by default 
  and are named according to the date and time to avoid overwriting.
* PySPectro software version is now displayed in instrument info window.
* Added licensing support for new SpectroCore v1.1. 
* Removed deprecated user guide.

###SpectroCore Versions Supported

* SpectroCore v1.1.231

###Bug Fixes and improvements

* Improved thread lock effciency in acquisition controller


##Version 1.0.1

###Description: 

This release includes an updated user guide that describes the 
Anaconda-based installation process.

###SpectroCore Versions Supported

* SpectroCore v1.0.229

###Bug Fixes

* Use python2.7 compliant package name for Queue
* Fix a crash that occurs if drivers are not installed
* Slightly improved handling of connection failure that occurs 
   when drivers are not installed.
* Changing exe command to pyspectro instead of run-pyspectro



##Version 1.0

Initial Release


