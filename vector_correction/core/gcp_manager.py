# -*- coding: utf-8 -*-
"""GCP manager

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

from typing import Dict

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QMouseEvent, QColor

from qgis.core import (
    QgsPointXY,
    QgsGeometry,
    QgsRectangle,
    QgsWkbTypes
)
from qgis.analysis import (
    QgsGcpTransformerInterface,
    QgsGcpGeometryTransformer
)

from qgis.gui import (
    QgsMapToolDigitizeFeature,
    QgsMapToolCapture,
    QgsMapCanvas,
    QgsAdvancedDigitizingDockWidget,
    QgsMapMouseEvent,
    QgsRubberBand
)


class GcpManager:
    """
    Manages a collection of GCPs
    """

    def __init__(self, map_canvas: QgsMapCanvas):
        self.map_canvas = map_canvas
        self.gcps = []
        self.rubber_bands = []

    def clear(self):
        """
        Clears the GCP manager
        """
        for band in self.rubber_bands:
            self.map_canvas.scene().removeItem(band)
        self.rubber_bands = []
        self.gcps = []

    def add_gcp(self, origin: QgsPointXY, destination: QgsPointXY):
        """
        Adds a GCP
        """
        self.gcps.append((origin, destination))

        rubber_band = QgsRubberBand(self.map_canvas, QgsWkbTypes.LineGeometry)
        rubber_band.addPoint(origin, False)
        rubber_band.addPoint(destination, True)
        rubber_band.setStrokeColor(QColor(255,0,0))

        self.rubber_bands.append(rubber_band)

    def to_gcp_transformer(self):
        """
        Creates a GCP transformer using the points added to this manager
        """
        return QgsGcpTransformerInterface.createFromParameters(QgsGcpTransformerInterface.TransformMethod.PolynomialOrder1,
                                                               [p[0] for p in self.gcps], [p[1] for p in self.gcps])

    def transform_features(self, features: Dict[int, QgsGeometry], extent: QgsRectangle):
        """
        Transforms the specified set of geometries
        """

        gcp_transformer = self.to_gcp_transformer()
        transformer = QgsGcpGeometryTransformer(gcp_transformer)

        return {
          _id: GcpManager.transform_vertices_in_extent(transformer, geom, extent)
          for _id, geom in features.items()
        }

    @staticmethod
    def transform_vertices_in_extent(transformer: QgsGcpGeometryTransformer, geometry: QgsGeometry, extent: QgsRectangle) -> QgsGeometry:
        """
        Transforms only the vertices within the specified extent
        """
        to_transform = {}

        for n, point in enumerate(geometry.vertices()):
            if extent.contains(QgsPointXY(point.x(), point.y())):
                to_transform[n] = point

        for n, point in to_transform.items():
            ok, transformed_x, transformed_y = transformer.gcpTransformer().transform(point.x(), point.y())
            if not ok:
                return QgsGeometry()

            geometry.moveVertex(transformed_x, transformed_y, n)

        return geometry







