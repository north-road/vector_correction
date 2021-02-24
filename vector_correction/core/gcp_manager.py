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

from dataclasses import dataclass
from typing import Dict, List

from qgis.PyQt.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QObject
)
from qgis.PyQt.QtGui import QColor
from qgis.analysis import (
    QgsGcpTransformerInterface,
    QgsGcpGeometryTransformer
)
from qgis.core import (
    QgsPointXY,
    QgsGeometry,
    QgsRectangle,
    QgsWkbTypes,
    QgsLineSymbol,
    QgsCoordinateReferenceSystem
)
from qgis.gui import (
    QgsMapCanvas,
    QgsRubberBand
)


@dataclass
class Gcp:
    """
    Encapsulates a GCP
    """
    origin: QgsPointXY
    destination: QgsPointXY
    crs: QgsCoordinateReferenceSystem


class GcpManager(QAbstractTableModel):
    """
    Manages a collection of GCPs
    """

    COLUMN_ID = 0
    COLUMN_ORIGIN_X = 1
    COLUMN_ORIGIN_Y = 2
    COLUMN_DESTINATION_X = 3
    COLUMN_DESTINATION_Y = 4

    gcps: List[Gcp]
    rubber_bands: List[QgsRubberBand]

    def __init__(self, map_canvas: QgsMapCanvas, parent: QObject = None):
        super().__init__(parent)
        self.map_canvas = map_canvas
        self.gcps = []
        self.rubber_bands = []

    def rowCount(self,  # pylint: disable=missing-function-docstring
                 parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.gcps)

    def columnCount(self,  # pylint: disable=missing-function-docstring
                    parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return 5

    def data(self,  # pylint: disable=missing-function-docstring, too-many-return-statements
             index: QModelIndex,
             role: int = Qt.DisplayRole):
        if index.row() < 0 or index.row() >= len(self.gcps):
            return None

        if role in (Qt.DisplayRole, Qt.ToolTipRole, Qt.EditRole):
            if index.column() == GcpManager.COLUMN_ID:
                return index.row() + 1
            if index.column() == GcpManager.COLUMN_ORIGIN_X:
                return self.gcps[index.row()].origin.x()
            if index.column() == GcpManager.COLUMN_ORIGIN_Y:
                return self.gcps[index.row()].origin.y()
            if index.column() == GcpManager.COLUMN_DESTINATION_X:
                return self.gcps[index.row()].destination.x()
            if index.column() == GcpManager.COLUMN_DESTINATION_Y:
                return self.gcps[index.row()].destination.y()

        return None

    def clear(self):
        """
        Clears the GCP manager
        """
        if not self.gcps:
            return

        self.beginRemoveRows(QModelIndex(), 0, len(self.gcps) - 1)
        for band in self.rubber_bands:
            self.map_canvas.scene().removeItem(band)
        self.rubber_bands = []
        self.gcps = []
        self.endRemoveRows()

    def add_gcp(self, origin: QgsPointXY, destination: QgsPointXY, crs: QgsCoordinateReferenceSystem):
        """
        Adds a GCP
        """
        self.beginInsertRows(QModelIndex(), len(self.gcps), len(self.gcps))
        self.gcps.append(Gcp(origin=origin, destination=destination, crs=crs))
        self.endInsertRows()

        rubber_band = self._create_rubber_band()
        rubber_band.addPoint(origin, False)
        rubber_band.addPoint(destination, True)
        rubber_band.setStrokeColor(QColor(255, 0, 0))

        self.rubber_bands.append(rubber_band)

    def _create_rubber_band(self) -> QgsRubberBand:
        """
        Creates a new rubber band
        """
        rubber_band = QgsRubberBand(self.map_canvas, QgsWkbTypes.LineGeometry)
        rubber_band.setSymbol(QgsLineSymbol.createSimple({'line_color': '#0000ff',
                                                          'line_width': 1,
                                                          'capstyle': 'round'}))
        return rubber_band

    def to_gcp_transformer(self):
        """
        Creates a GCP transformer using the points added to this manager
        """
        return QgsGcpTransformerInterface.createFromParameters(
            QgsGcpTransformerInterface.TransformMethod.PolynomialOrder1,
            [p.origin for p in self.gcps], [p.destination for p in self.gcps])

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
    def transform_vertices_in_extent(transformer: QgsGcpGeometryTransformer, geometry: QgsGeometry,
                                     extent: QgsRectangle) -> QgsGeometry:
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
