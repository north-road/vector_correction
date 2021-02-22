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
from qgis.PyQt.QtGui import QMouseEvent

from qgis.core import (
    QgsPointXY,
    QgsGeometry
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
    QgsMapMouseEvent
)


class GcpManager:
    """
    Manages a collection of GCPs
    """

    def __init__(self):
        self.gcps = []

    def add_gcp(self, origin: QgsPointXY, destination: QgsPointXY):
        """
        Adds a GCP
        """
        self.gcps.append((origin, destination))

    def to_gcp_transformer(self):
        """
        Creates a GCP transformer using the points added to this manager
        """
        return QgsGcpTransformerInterface.createFromParameters(QgsGcpTransformerInterface.TransformMethod.Projective,
                                                               [p[0] for p in self.gcps], [p[1] for p in self.gcps])

    def transform_features(self, features: Dict[int, QgsGeometry]):
        """
        Transforms the specified set of geometries
        """

        gcp_transformer = self.to_gcp_transformer()
        transformer = QgsGcpGeometryTransformer(gcp_transformer)

        return {
          _id: transformer.transform(geom)[0]
          for _id, geom in features.items()
        }




