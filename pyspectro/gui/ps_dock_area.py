# -----------------------------------------------------------------------------
# Copyright (c) 2016-2021, DSPlogic, Inc.  All Rights Reserved.
#
# RESTRICTED RIGHTS
# Use of this software is permitted only with a software license agreement.
#
# Details of the software license agreement are in the file LICENSE.txt,
# distributed with this software.
# -----------------------------------------------------------------------------

from enaml.layout.api import (
    vbox,
    hbox,
    grid,
    spacer,
    DockLayout,
    HSplitLayout,
    VSplitLayout,
    TabLayout,
    InsertItem,
    align,
)
from enaml.widgets.api import (
    MainWindow,
    Container,
    DockArea,
    DockItem,
    PushButton,
    Slider,
    MenuBar,
    Menu,
    Action,
    Timer,
    Html,
    Form,
    Label,
    Field,
    ObjectCombo,
    CheckBox,
    MultilineField,
    IPythonConsole,
    MPLCanvas,
    ToolBar,
    GroupBox,
    ComboBox,
    RadioButton,
    SpinBox,
)
from enaml.stdlib.fields import IntField, FloatField


from pyspectro.gui.channel_view import ChannelDockItem, ChannelWindow
from pyspectro.gui.pyspectro_model import SpectroModel

from atom.api import Atom, Typed, observe, Value


from pyspectro.gui.pyspectro_top import ConsoleView, CalibrationView
from pyspectro.gui.inputsettings_view import InputSettingsView
from pyspectro.gui.spectral_view import SpectralView
from pyspectro.gui.monitor_view import MonitorView
from pyspectro.gui.cwtest_view import CwTestView
from pyspectro.gui.acq_control_view import AcquisitionControlView
from pyspectro.gui.datalogger_control_view import DataLoggerControlView

# from pyspectro.gui.ps_dock_area_view import PsDockArea


class MainAreaController(Atom):

    model = Typed(SpectroModel)
    view = Value()  # ForwardTyped(lambda: PsDockArea)

    def initialize_layout(self):
        initialize_layout(self.view)

    def close_dock_layout(self):
        close_dock_layout(self.view)

    @observe("model.connectionSignal")
    def new_popup(self, connected):
        if connected:
            self.initialize_layout()
            # information(None, 'Info Dialog', 'Connected.')
        else:
            self.close_dock_layout()
            # information(None, 'Info Dialog', 'Disconnected.')


def initialize_layout(mainArea):

    name = "spectrum_1"
    title = "Spectrum 1"
    item = DockItem(mainArea, name=name, title=title)
    SpectralView(item, spectrumFigure=mainArea.spectroModel.spectrumFigure)
    op = InsertItem(item=name)

    mainArea.update_layout(op)

    name = "acq_tab"
    title = "Acquisition"
    item = DockItem(mainArea, name=name, title=title, closable=False)
    AcquisitionControlView(item, model=mainArea.spectroModel)
    op = InsertItem(item=name)

    mainArea.update_layout(op)

    name = "datalogger_tab"
    title = "Data Logging"
    item = DockItem(mainArea, name=name, title=title, closable=False)
    DataLoggerControlView(item, model=mainArea.spectroModel)
    op = InsertItem(item=name)

    mainArea.update_layout(op)

    name = "Monitor"
    title = "Monitor"
    item = DockItem(mainArea, name=name, title=title, closable=False)
    MonitorView(item, model=mainArea.spectroModel)
    op = InsertItem(item=name)

    mainArea.update_layout(op)

    name = "input_settings"
    title = "Input Settings"
    item = DockItem(mainArea, name=name, title=title, closable=False)
    InputSettingsView(item, model=mainArea.spectroModel)
    op = InsertItem(item=name)

    mainArea.update_layout(op)

    #     name  = 'console'
    #     title = 'Console'
    #     item    = DockItem(mainArea, name=name, title=title, closable = False)
    #     ConsoleView(item, model = mainArea.spectroModel)
    #     op      = InsertItem(item = name)
    #
    #     mainArea.update_layout(op)

    name = "cal_tab"
    title = "Calibration"
    item = DockItem(mainArea, name=name, title=title, closable=False)
    CalibrationView(item, model=mainArea.spectroModel)
    op = InsertItem(item=name)

    mainArea.update_layout(op)

    name = "cwtest_tab"
    title = "Test Input"
    item = DockItem(mainArea, name=name, title=title, closable=False)
    CwTestView(item, cwTestModel=mainArea.spectroModel.cwTestModel)
    op = InsertItem(item=name)

    mainArea.update_layout(op)

    layout = HSplitLayout(
        VSplitLayout(TabLayout("spectrum_1"), "Monitor"),
        VSplitLayout(
            TabLayout("acq_tab", "cal_tab", "datalogger_tab"),
            TabLayout("input_settings", "cwtest_tab"),
        ),
    )

    dockLayout = DockLayout(layout)
    # dockLayout.items.append()

    mainArea.apply_layout(dockLayout)


def close_dock_layout(mainArea):
    for item in mainArea.dock_items():
        item.destroy()
