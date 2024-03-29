# coding=utf-8
"""GCP Manager Test.

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

import unittest

from qgis.analysis import QgsGcpTransformerInterface
from qgis.core import (
    QgsPointXY,
    QgsCoordinateReferenceSystem,
    QgsSettings
)
from qgis.gui import QgsMapCanvas

from vector_correction.core.gcp_manager import (
    GcpManager,
    Gcp,
    NotEnoughGcpsException,
    TransformCreationException
)
from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class GCPManagerTest(unittest.TestCase):
    """Test GCP Manager works."""

    def test_empty(self):
        """
        Test empty manager
        """
        canvas = QgsMapCanvas()
        manager = GcpManager(canvas)
        self.assertFalse(manager.gcps)
        self.assertFalse(manager.rubber_bands)

        self.assertEqual(manager.rowCount(), 0)
        self.assertFalse(manager.data(manager.index(0, 0)))
        self.assertFalse(manager.data(manager.index(0, 1)))
        self.assertFalse(manager.data(manager.index(0, 2)))

    def test_gcps(self):
        """
        Test adding GCPs
        """
        canvas = QgsMapCanvas()
        manager = GcpManager(canvas)

        manager.add_gcp(QgsPointXY(10, 11), QgsPointXY(20, 22), crs=QgsCoordinateReferenceSystem('EPSG:4326'))

        self.assertEqual(manager.rowCount(), 1)
        self.assertEqual(manager.data(manager.index(0, 0)), 1)
        self.assertEqual(manager.data(manager.index(0, 1)), '10.00')
        self.assertEqual(manager.data(manager.index(0, 2)), '11.00')
        self.assertEqual(manager.data(manager.index(0, 3)), '20.00')
        self.assertEqual(manager.data(manager.index(0, 4)), '22.00')

        self.assertEqual(manager.gcps,
                         [Gcp(QgsPointXY(10, 11), QgsPointXY(20, 22), QgsCoordinateReferenceSystem('EPSG:4326'))])
        self.assertEqual(len(manager.rubber_bands), 1)

        manager.add_gcp(QgsPointXY(100, 101), QgsPointXY(200, 202), crs=QgsCoordinateReferenceSystem('EPSG:3111'))

        self.assertEqual(manager.rowCount(), 2)
        self.assertEqual(manager.data(manager.index(0, 0)), 1)
        self.assertEqual(manager.data(manager.index(0, 1)), '10.00')
        self.assertEqual(manager.data(manager.index(0, 2)), '11.00')
        self.assertEqual(manager.data(manager.index(0, 3)), '20.00')
        self.assertEqual(manager.data(manager.index(0, 4)), '22.00')
        self.assertEqual(manager.data(manager.index(1, 0)), 2)
        self.assertEqual(manager.data(manager.index(1, 1)), '100.00')
        self.assertEqual(manager.data(manager.index(1, 2)), '101.00')
        self.assertEqual(manager.data(manager.index(1, 3)), '200.00')
        self.assertEqual(manager.data(manager.index(1, 4)), '202.00')

        self.assertEqual(manager.gcps,
                         [Gcp(QgsPointXY(10, 11), QgsPointXY(20, 22), QgsCoordinateReferenceSystem('EPSG:4326')),
                          Gcp(QgsPointXY(100, 101), QgsPointXY(200, 202), QgsCoordinateReferenceSystem('EPSG:3111'))])
        self.assertEqual(len(manager.rubber_bands), 2)

        manager.clear()
        self.assertEqual(manager.rowCount(), 0)
        self.assertFalse(manager.data(manager.index(0, 0)))
        self.assertFalse(manager.data(manager.index(0, 1)))
        self.assertFalse(manager.data(manager.index(0, 2)))
        self.assertFalse(manager.gcps)
        self.assertFalse(manager.rubber_bands)

    def test_create_transform(self):
        """
        Test creating transforms
        """

        settings = QgsSettings()
        settings.setValue('vector_corrections/method', int(QgsGcpTransformerInterface.TransformMethod.PolynomialOrder1),
                          QgsSettings.Plugins)

        canvas = QgsMapCanvas()
        manager = GcpManager(canvas)
        with self.assertRaises(NotEnoughGcpsException):
            manager.to_gcp_transformer(QgsCoordinateReferenceSystem('EPSG:4326'))

        manager.add_gcp(QgsPointXY(10, 11), QgsPointXY(20, 22), crs=QgsCoordinateReferenceSystem('EPSG:4326'))
        manager.add_gcp(QgsPointXY(12, 13), QgsPointXY(21, 24), crs=QgsCoordinateReferenceSystem('EPSG:4326'))
        manager.add_gcp(QgsPointXY(11, 15), QgsPointXY(23, 25), crs=QgsCoordinateReferenceSystem('EPSG:4326'))

        self.assertIsNotNone(manager.to_gcp_transformer(QgsCoordinateReferenceSystem('EPSG:4326')))

        manager.clear()

        manager.add_gcp(QgsPointXY(10, 11), QgsPointXY(20, 22), crs=QgsCoordinateReferenceSystem('EPSG:4326'))
        manager.add_gcp(QgsPointXY(10, 11), QgsPointXY(20, 22), crs=QgsCoordinateReferenceSystem('EPSG:4326'))
        manager.add_gcp(QgsPointXY(10, 11), QgsPointXY(20, 22), crs=QgsCoordinateReferenceSystem('EPSG:4326'))

        with self.assertRaises(TransformCreationException):
            manager.to_gcp_transformer(QgsCoordinateReferenceSystem('EPSG:4326'))


if __name__ == "__main__":
    suite = unittest.makeSuite(GCPManagerTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
