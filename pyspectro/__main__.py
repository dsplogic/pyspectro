# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
# -----------------------------------------------------------------------------

from enaml.qt.qt_application import QtApplication
import enaml
import sys, os
import pyspectro.gui
import types
import time

#: Enable logging for main thread
import logging

#: Data log file
HOME = os.path.expanduser("~")
PYHOME = os.path.join(HOME, "pyspectro")

if not os.path.exists(PYHOME):
    os.makedirs(PYHOME)

timestr = time.strftime("%Y%m%d_%H%M%S")
fname = "%s-pyspectro_log.txt" % timestr
logfilename = os.path.join(PYHOME, fname)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(relativeCreated)5d %(threadName)10s %(levelname)-8s %(message)-60s  <%(name)-15s>",
    filename=logfilename,
    filemode="w",
)

#: Add console StreamHandler to RootLogger
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(relativeCreated)5d %(levelname)-8s %(message)-60s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)


def main():

    # sys.path.insert(0, os.path.normpath(pyspectro.gui.__path__[0]) )

    enaml_file = os.path.join(pyspectro.gui.__path__[0], "pyspectro_top.enaml")
    module = types.ModuleType("__main__")
    module.__file__ = os.path.abspath(enaml_file)

    sys.modules["__main__"] = module
    ns = module.__dict__

    with enaml.imports():
        from pyspectro.gui.pyspectro_view import Main

    app = QtApplication()
    # Create a view and show it.
    ns["Main"] = Main
    view = ns["Main"]()
    view.show()
    view.send_to_front()

    # import cProfile
    # cProfile.runctx('app.start()', globals(), locals())

    app.start()


if __name__ == "__main__":

    """Setup logging"""

    main()
