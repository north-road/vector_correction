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

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QMouseEvent

from qgis.gui import (
    QgsMapToolDigitizeFeature,
    QgsMapToolCapture,
    QgsMapCanvas,
    QgsAdvancedDigitizingDockWidget,
    QgsMapMouseEvent
)


class DrawLineTool(QgsMapToolDigitizeFeature):
    """
    A map tool for drawing lines
    """

    def __init__(self, map_canvas: QgsMapCanvas, cad_dock_widget: QgsAdvancedDigitizingDockWidget):
        super().__init__(map_canvas, cad_dock_widget, QgsMapToolCapture.CaptureLine)

    def cadCanvasReleaseEvent(self, e):

        if e.button() == Qt.LeftButton and self.captureCurve().numPoints() > 0:
            super().cadCanvasReleaseEvent(e)
            # second click = finish

            finish_event = QgsMapMouseEvent(self.canvas(), QMouseEvent(e.type(), e.localPos(), Qt.RightButton, e.buttons(), e.modifiers()) )
            super().cadCanvasReleaseEvent(finish_event)
        else:
            super().cadCanvasReleaseEvent(e)

