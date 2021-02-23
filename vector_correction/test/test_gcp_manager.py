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

from qgis.core import QgsPointXY
from qgis.gui import QgsMapCanvas

from vector_correction.core.gcp_manager import GcpManager
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

        manager.add_gcp(QgsPointXY(10, 11), QgsPointXY(20, 22))

        self.assertEqual(manager.rowCount(), 1)
        self.assertEqual(manager.data(manager.index(0, 0)), 1)
        self.assertEqual(manager.data(manager.index(0, 1)), 10.0)
        self.assertEqual(manager.data(manager.index(0, 2)), 11.0)
        self.assertEqual(manager.data(manager.index(0, 3)), 20.0)
        self.assertEqual(manager.data(manager.index(0, 4)), 22.0)

        self.assertEqual(manager.gcps, [(QgsPointXY(10, 11), QgsPointXY(20, 22))])
        self.assertEqual(len(manager.rubber_bands), 1)

        manager.add_gcp(QgsPointXY(100, 101), QgsPointXY(200, 202))

        self.assertEqual(manager.rowCount(), 2)
        self.assertEqual(manager.data(manager.index(0, 0)), 1)
        self.assertEqual(manager.data(manager.index(0, 1)), 10.0)
        self.assertEqual(manager.data(manager.index(0, 2)), 11.0)
        self.assertEqual(manager.data(manager.index(0, 3)), 20.0)
        self.assertEqual(manager.data(manager.index(0, 4)), 22.0)
        self.assertEqual(manager.data(manager.index(1, 0)), 2)
        self.assertEqual(manager.data(manager.index(1, 1)), 100.0)
        self.assertEqual(manager.data(manager.index(1, 2)), 101.0)
        self.assertEqual(manager.data(manager.index(1, 3)), 200.0)
        self.assertEqual(manager.data(manager.index(1, 4)), 202.0)

        self.assertEqual(manager.gcps, [(QgsPointXY(10, 11), QgsPointXY(20, 22)),
                                        (QgsPointXY(100, 101), QgsPointXY(200, 202))])
        self.assertEqual(len(manager.rubber_bands), 2)

        manager.clear()
        self.assertEqual(manager.rowCount(), 0)
        self.assertFalse(manager.data(manager.index(0, 0)))
        self.assertFalse(manager.data(manager.index(0, 1)))
        self.assertFalse(manager.data(manager.index(0, 2)))
        self.assertFalse(manager.gcps)
        self.assertFalse(manager.rubber_bands)


if __name__ == "__main__":
    suite = unittest.makeSuite(GCPManagerTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
