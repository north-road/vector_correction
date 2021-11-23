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
    Qgis,
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
    QgsRubberBand,
    QgsMessageBar,
    QgsAbstractMapToolHandler
)

from vector_correction.core.settings_registry import SETTINGS_REGISTRY


class DrawLineTool(QgsMapToolDigitizeFeature):
    """
    A map tool for drawing lines
    """

    MAX_PREVIEW_GEOMETRIES = 10000

    def __init__(self,
                 map_canvas: QgsMapCanvas,
                 cad_dock_widget: QgsAdvancedDigitizingDockWidget,
                 message_bar: QgsMessageBar):
        super().__init__(map_canvas, cad_dock_widget, QgsMapToolCapture.CaptureLine)
        self.message_bar = message_bar
        self.temporary_geometries = []
        self.rubber_band = None
        self.start_point = None

    def cadCanvasMoveEvent(self, e):  # pylint: disable=missing-function-docstring
        if self.rubber_band:
            self.rubber_band.setTranslationOffset(e.mapPoint().x() - self.start_point.x(),
                                                  e.mapPoint().y() - self.start_point.y())

        super().cadCanvasMoveEvent(e)

    def cadCanvasReleaseEvent(self, e):  # pylint: disable=missing-function-docstring
        if self.rubber_band is not None:
            self.canvas().scene().removeItem(self.rubber_band)
            self.rubber_band = None

        if e.button() == Qt.LeftButton and self.captureCurve().numPoints() > 0:  # pylint: disable=too-many-nested-blocks
            super().cadCanvasReleaseEvent(e)

            # second click = finish
            finish_event = QgsMapMouseEvent(self.canvas(),
                                            QMouseEvent(e.type(), e.localPos(), Qt.RightButton, e.buttons(),
                                                        e.modifiers()))

            super().cadCanvasReleaseEvent(finish_event)
        else:
            if e.button() == Qt.LeftButton:
                # collect visible geometries to move
                self.start_point = e.mapPoint()

                geometries = []

                extent = self.canvas().mapSettings().visibleExtent()
                for _, layer in QgsProject.instance().mapLayers().items():
                    if isinstance(layer, QgsVectorLayer) and layer.isEditable():
                        request = QgsFeatureRequest()
                        request.setDestinationCrs(self.canvas().mapSettings().destinationCrs(),
                                                  QgsProject.instance().transformContext())
                        request.setFilterRect(extent)
                        request.setNoAttributes()

                        for f in layer.getFeatures(request):
                            geometries.append(f.geometry())

                            if len(geometries) > DrawLineTool.MAX_PREVIEW_GEOMETRIES:
                                break

                    if len(geometries) > DrawLineTool.MAX_PREVIEW_GEOMETRIES:
                        break

                if geometries:
                    self.rubber_band = QgsRubberBand(self.canvas(), QgsWkbTypes.LineGeometry)
                    self.rubber_band.setStrokeColor(SETTINGS_REGISTRY.preview_color())
                    for g in geometries:
                        self.rubber_band.addGeometry(g, doUpdate=False)

                    self.rubber_band.updatePosition()
                    self.rubber_band.update()
                else:
                    self.message_bar.pushMessage(None,
                                                 self.tr('No visible layers are set to allow edits'),
                                                 Qgis.Warning, duration=QgsMessageBar.defaultMessageTimeout(Qgis.Info))

            super().cadCanvasReleaseEvent(e)


class DrawLineToolHandler(QgsAbstractMapToolHandler):
    """
    Handler for the draw correction tool
    """

    def isCompatibleWithLayer(self, layer, context):  # pylint: disable=unused-argument,missing-function-docstring
        return True
