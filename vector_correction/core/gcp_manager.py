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
from qgis.PyQt.QtGui import (
    QColor
)
from qgis.analysis import (
    QgsGcpTransformerInterface,
    QgsGcpGeometryTransformer
)
from qgis.core import (
    QgsPoint,
    QgsPointXY,
    QgsGeometry,
    QgsLineString,
    QgsLineSymbol,
    QgsRectangle,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsMarkerLineSymbolLayer,
    QgsTemplatedLineSymbolLayerBase,
    QgsMarkerSymbol,
    QgsFontMarkerSymbolLayer
)
from qgis.gui import (
    QgsMapCanvas,
    QgsRubberBand
)

from vector_correction.core.settings_registry import SettingsRegistry


@dataclass
class Gcp:
    """
    Encapsulates a GCP
    """
    origin: QgsPointXY
    destination: QgsPointXY
    crs: QgsCoordinateReferenceSystem


class NotEnoughGcpsException(Exception):
    """
    Raised when not enough GCPs are defined for the selected transform method
    """


class TransformCreationException(Exception):
    """
    Raised when transform could not be created (eg due to colinear points)
    """


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

        rubber_band = self._create_rubber_band(len(self.gcps))
        rubber_band.setToGeometry(QgsGeometry(QgsLineString(QgsPoint(origin), QgsPoint(destination))), crs)

        self.rubber_bands.append(rubber_band)

    def _rubber_band_symbol_for_row(self, row_number: int) -> QgsLineSymbol:
        """
        Creates the line symbol for the specified row
        """
        symbol = SettingsRegistry.arrow_symbol()

        label_marker = QgsMarkerLineSymbolLayer(False)
        label_marker.setPlacement(QgsTemplatedLineSymbolLayerBase.FirstVertex)

        label_marker_sub_symbol = QgsMarkerSymbol()
        font_marker = QgsFontMarkerSymbolLayer('Arial', str(row_number), 5)
        font_marker.setFontStyle('Bold')
        font_marker.setColor(QColor(0,0,0))
        font_marker.setStrokeColor(QColor(255, 255, 255))
        font_marker.setStrokeWidth(0.3)
        label_marker_sub_symbol.changeSymbolLayer(0, font_marker)
        label_marker.setSubSymbol(label_marker_sub_symbol)
        symbol.appendSymbolLayer(label_marker)

        return symbol

    def _create_rubber_band(self, row_number: int) -> QgsRubberBand:
        """
        Creates a new rubber band
        """
        rubber_band = QgsRubberBand(self.map_canvas, QgsWkbTypes.LineGeometry)
        rubber_band.setSymbol(self._rubber_band_symbol_for_row(row_number))
        return rubber_band

    def update_line_symbols(self):
        """
        Updates all existing rubber bands to the current arrow symbol
        """
        for row_number, band in enumerate(self.rubber_bands):
            band.setSymbol(self._rubber_band_symbol_for_row(row_number + 1))
            band.update()

    def to_gcp_transformer(self, destination_crs: QgsCoordinateReferenceSystem):
        """
        Creates a GCP transformer using the points added to this manager
        """
        current_method = SettingsRegistry.transform_method()

        gcp_transformer = QgsGcpTransformerInterface.create(current_method)
        if len(self.gcps) < gcp_transformer.minimumGcpCount():
            raise NotEnoughGcpsException(
                self.tr('{} transformation requires at least {} points').format(
                    QgsGcpTransformerInterface.methodToString(current_method),
                    gcp_transformer.minimumGcpCount()))

        origin_points = []
        destination_points = []

        for gcp in self.gcps:
            ct = QgsCoordinateTransform(gcp.crs, destination_crs, QgsProject.instance().transformContext())
            origin_points.append(ct.transform(gcp.origin))
            destination_points.append(ct.transform(gcp.destination))

        if not gcp_transformer.updateParametersFromGcps(origin_points,
                                                        destination_points):
            raise TransformCreationException(self.tr('Could not create transform from the defined GCPs'))

        return gcp_transformer

    def transform_features(self,
                           features: Dict[int, QgsGeometry],
                           feature_crs: QgsCoordinateReferenceSystem,
                           extent: QgsRectangle,
                           extent_crs: QgsCoordinateReferenceSystem
                           ):
        """
        Transforms the specified set of geometries
        """
        gcp_transformer = self.to_gcp_transformer(feature_crs)
        transformer = QgsGcpGeometryTransformer(gcp_transformer)

        feature_to_extent_transform = QgsCoordinateTransform(feature_crs,
                                                             extent_crs,
                                                             QgsProject.instance().transformContext())

        return {
            _id: GcpManager.transform_vertices_in_extent(transformer, geom, extent, feature_to_extent_transform)
            for _id, geom in features.items()
        }

    @staticmethod
    def transform_vertices_in_extent(transformer: QgsGcpGeometryTransformer,
                                     geometry: QgsGeometry,
                                     extent: QgsRectangle,
                                     geometry_to_extent_transform: QgsCoordinateTransform) -> QgsGeometry:
        """
        Transforms only the vertices within the specified extent
        """
        to_transform = {}

        for n, point in enumerate(geometry.vertices()):
            # transform point to extent crs, in order to check exact intersection of the point and the visible extent
            transformed_point = geometry_to_extent_transform.transform(QgsPointXY(point.x(), point.y()))

            if extent.contains(transformed_point):
                to_transform[n] = point

        for n, point in to_transform.items():
            ok, transformed_x, transformed_y = transformer.gcpTransformer().transform(point.x(), point.y())
            if not ok:
                return QgsGeometry()

            geometry.moveVertex(transformed_x, transformed_y, n)

        return geometry
