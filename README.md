# PySpectro Demonstration Software

## Installation

Ensure that Python 3.8 is installed in the base system.

Unzip or clone the PySpectro software to a working directory (e.g.).

    c:\work\pyspectro

Create and activate a [virtual environment](https://docs.python.org/3/library/venv.html).  In this example, the virtual environment is 
located in a subfolder called `tenv`:

    Linux:
    
        python3 -m venv tenv
        source tenv/bin/activate
    
    Windows:
    
        py -m venv tenv
        tenv\Scripts\activate.bat

Install the prerequisite software into the virtual environment:

    pip install -r requirements.txt

Install pyspectro into the virtual environment:

    pip install -e .

Launch the pyspectro software:

    pyspectro

Note that the virtual environment must be activated each time prior to running pyspectro.