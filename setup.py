#------------------------------------------------------------------------------
# Copyright (c) 2016, DSPlogic, Inc.  All Rights Reserved.  
# 
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt, 
# distributed with this software.
#------------------------------------------------------------------------------
from __future__ import (division, print_function, absolute_import)

import os

from setuptools import setup, find_packages, Extension

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def get_version():
    """ Get version from ._version.py file 
        (setup should not import this package) """    
    import re
    VERSIONFILE="pyspectro/_version.py"
    verstrline = open(VERSIONFILE, "rt").read()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        verstr = mo.group(1)
        return verstr
    else:
        raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(
    name='pyspectro',
    version=get_version(),
    description='DSPlogic Wideband FFT Spectrometer GUI',
    long_description=read('README.md'),
    package_data={'': ['*.enaml', 'gui/icons/*.png']},
    packages=find_packages(exclude=['test', 'examples']),
    keywords='spectrometer, fft',
    author='DSPlogic, Inc.',
    author_email='inforequest@dsplogic.com',
    url='http://www.dsplogic.com',
    license='Licensed with restricted rights.  See LICENSE.txt for details',
    entry_points={'console_scripts': ['run-pyspectro = pyspectro.__main__:main']}
    #ext_modules=ext_modules,
)
