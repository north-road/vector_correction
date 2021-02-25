# -*- coding: utf-8 -*-
"""Draw line tool

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '20/04/2018'
__copyright__ = 'Copyright 2018, North Road'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QAction
)
from qgis.analysis import (
    QgsGcpTransformerInterface
)
from qgis.core import QgsSettings
from qgis.gui import (
    QgsPanelWidget,
    QgsDockWidget,
    QgsPanelWidgetStack
)

from vector_correction.core.gcp_manager import GcpManager
from vector_correction.gui.gui_utils import GuiUtils

WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('point_list.ui'))


class PointListWidget(QgsPanelWidget, WIDGET):
    """
    A table for gcp lists
    """

    def __init__(self, gcp_manager: GcpManager, parent: QWidget = None):
        super().__init__(parent)

        self.setupUi(self)

        self.gcp_manager = gcp_manager
        self.table_view.setModel(self.gcp_manager)

        self.settings_action = QAction(self.tr('Settings'), self)
        self.settings_action.triggered.connect(self._show_settings)
        self.toolbar.addAction(self.settings_action)

        self.settings_panel = None

    def _show_settings(self):
        """
        Shows the settings panel
        """
        self.settings_panel = SettingsWidget()
        self.settings_panel.panelAccepted.connect(self._update_settings)
        self.openPanel(self.settings_panel)

    def _update_settings(self):
        """
        Updates the stored settings
        """
        self.settings_panel.save_settings()
        self.settings_panel.deleteLater()
        self.settings_panel = None


SETTINGS_WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('settings.ui'))


class SettingsWidget(QgsPanelWidget, SETTINGS_WIDGET):
    """
    A table for gcp lists
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.setupUi(self)

        self.setPanelTitle(self.tr('Settings'))

        for method in [QgsGcpTransformerInterface.TransformMethod.Linear,
                       QgsGcpTransformerInterface.TransformMethod.Helmert,
                       QgsGcpTransformerInterface.TransformMethod.PolynomialOrder1,
                       QgsGcpTransformerInterface.TransformMethod.PolynomialOrder2,
                       QgsGcpTransformerInterface.TransformMethod.PolynomialOrder3,
                       QgsGcpTransformerInterface.TransformMethod.ThinPlateSpline,
                       QgsGcpTransformerInterface.TransformMethod.Projective
                       ]:
            self.combo_method.addItem(QgsGcpTransformerInterface.methodToString(method), int(method))

        self.restore_settings()

    def restore_settings(self):
        """
        Restores saved settings
        """
        settings = QgsSettings()
        current_method = settings.value('vector_corrections/method', 2, int, QgsSettings.Plugins)
        self.combo_method.setCurrentIndex(self.combo_method.findData(current_method))

    def save_settings(self):
        """
        Saves all configured settings
        """
        settings = QgsSettings()
        settings.setValue('vector_corrections/method', int(self.combo_method.currentData()), QgsSettings.Plugins)


class CorrectionsDockWidget(QgsDockWidget):
    """
    A dock widget container for plugin GUI components
    """

    def __init__(self, gcp_manager: GcpManager, parent=None):
        super().__init__(parent)

        self.gcp_manager = gcp_manager

        self.setObjectName('CorrectionsDockWidget')
        self.setWindowTitle(self.tr('Vector Corrections'))

        self.stack = QgsPanelWidgetStack()

        w = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.stack)
        w.setLayout(layout)
        self.setWidget(w)

        self.table_widget = PointListWidget(self.gcp_manager)
        self.table_widget.setDockMode(True)
        self.stack.setMainPanel(self.table_widget)
