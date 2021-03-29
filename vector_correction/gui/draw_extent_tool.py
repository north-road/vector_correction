# -*- coding: utf-8 -*-
"""Draw extent tool

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

from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import (
    QgsRectangle,
    QgsReferencedRectangle,
    QgsWkbTypes,
    QgsPointXY
)
from qgis.gui import (
    QgsMapToolExtent,
    QgsMapCanvas,
    QgsMessageBar,
    QgsAbstractMapToolHandler,
    QgsRubberBand
)

from vector_correction.core.settings_registry import SettingsRegistry


class DrawExtentTool(QgsMapToolExtent):
    """
    A map tool for drawing extents
    """

    extent_set = pyqtSignal(QgsReferencedRectangle)

    def __init__(self,
                 map_canvas: QgsMapCanvas,
                 message_bar: QgsMessageBar):
        super().__init__(map_canvas)
        self.message_bar = message_bar

        self.extentChanged.connect(self._on_extent_set)

        self.rubber_band = None

    def __del__(self):
        if self.rubber_band:
            self.canvas().scene().removeItem(self.rubber_band)
            del self.rubber_band

    def _on_extent_set(self, extent: QgsRectangle):
        """
        Triggered when the extent is drawn
        """
        self.clearRubberBand()
        self.extent_set.emit(QgsReferencedRectangle(extent, self.canvas().mapSettings().destinationCrs()))

        if self.rubber_band is None:
            self.rubber_band = QgsRubberBand(self.canvas(), QgsWkbTypes.PolygonGeometry)
            self.rubber_band.setSymbol(SettingsRegistry.extent_symbol())

        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        self.rubber_band.addPoint(QgsPointXY(extent.xMinimum(), extent.yMinimum()), False)
        self.rubber_band.addPoint(QgsPointXY(extent.xMaximum(), extent.yMinimum()), False)
        self.rubber_band.addPoint(QgsPointXY(extent.xMaximum(), extent.yMaximum()), False)
        self.rubber_band.addPoint(QgsPointXY(extent.xMinimum(), extent.yMaximum()), False)
        self.rubber_band.addPoint(QgsPointXY(extent.xMinimum(), extent.yMinimum()), True)

    def show_aoi(self, visible: bool):
        """
        Toggles the display of the AOI rubber band
        """
        if not self.rubber_band:
            return

        if visible:
            self.rubber_band.show()
        else:
            self.rubber_band.hide()

    def update_fill_symbol(self):
        """
        Updates existing rubber bands to the current extent symbol
        """
        if self.rubber_band:
            self.rubber_band.setSymbol(SettingsRegistry.extent_symbol())
            self.rubber_band.update()


class DrawExtentToolHandler(QgsAbstractMapToolHandler):
    """
    Handler for the draw extent tool
    """

    def isCompatibleWithLayer(self, layer, context):  # pylint: disable=unused-argument,missing-function-docstring
        return True
