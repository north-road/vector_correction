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
from qgis.PyQt.QtWidgets import QWidget

from qgis.gui import (
    QgsPanelWidget
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
