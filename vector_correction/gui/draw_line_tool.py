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

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsWkbTypes
)

from qgis.gui import (
    QgsMapToolDigitizeFeature,
    QgsMapToolCapture,
    QgsMapCanvas,
    QgsAdvancedDigitizingDockWidget,
    QgsMapMouseEvent,
    QgsRubberBand
)


class DrawLineTool(QgsMapToolDigitizeFeature):
    """
    A map tool for drawing lines
    """

    MAX_PREVIEW_GEOMETRIES = 10000

    def __init__(self, map_canvas: QgsMapCanvas, cad_dock_widget: QgsAdvancedDigitizingDockWidget):
        super().__init__(map_canvas, cad_dock_widget, QgsMapToolCapture.CaptureLine)

        self.temporary_geometries = []
        self.rubber_band = None
        self.start_point = None

    def cadCanvasMoveEvent(self, e):
        if self.rubber_band:
            self.rubber_band.setTranslationOffset(e.mapPoint().x() - self.start_point.x(),
            e.mapPoint().y() - self.start_point.y())

        super().cadCanvasMoveEvent(e)

    def cadCanvasReleaseEvent(self, e):

        if self.rubber_band is not None:
            self.canvas().scene().removeItem(self.rubber_band)
            self.rubber_band = None

        if e.button() == Qt.LeftButton and self.captureCurve().numPoints() > 0:
            super().cadCanvasReleaseEvent(e)
            # second click = finish

            finish_event = QgsMapMouseEvent(self.canvas(), QMouseEvent(e.type(), e.localPos(), Qt.RightButton, e.buttons(), e.modifiers()))

            super().cadCanvasReleaseEvent(finish_event)
        else:
            if e.button() == Qt.LeftButton:
                # collect visible geometries to move
                self.start_point = e.mapPoint()

                geometries = []

                extent = self.canvas().mapSettings().visibleExtent()
                for _, layer in QgsProject.instance().mapLayers().items():
                    if isinstance(layer, QgsVectorLayer) and layer.isEditable():
                        for f in layer.getFeatures(QgsFeatureRequest().setFilterRect(extent).setNoAttributes()):
                            geometries.append(f.geometry())

                            if len(geometries) > DrawLineTool.MAX_PREVIEW_GEOMETRIES:
                                break

                    if len(geometries) > DrawLineTool.MAX_PREVIEW_GEOMETRIES:
                        break

                if geometries:
                    self.rubber_band = QgsRubberBand(self.canvas(), QgsWkbTypes.LineGeometry)
                    for g in geometries:
                        self.rubber_band.addGeometry(g, doUpdate=False)

                    self.rubber_band.updatePosition()
                    self.rubber_band.update()

            super().cadCanvasReleaseEvent(e)

