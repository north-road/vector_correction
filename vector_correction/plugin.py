# -*- coding: utf-8 -*-
"""QGIS Vector Correction plugin

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2021 by Nyall Dawson'
__date__ = '22/02/2021'
__copyright__ = 'Copyright 2021, North Road'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtCore import (
    Qt,
    QTranslator,
    QCoreApplication
)
from qgis.PyQt.QtWidgets import (
    QToolBar,
    QAction
)
from qgis.core import (
    QgsApplication,
    QgsVectorLayer,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsFeature,
    QgsPointXY,
    QgsFeatureRequest,
    QgsCoordinateTransform
)
from qgis.gui import (
    QgisInterface
)

from vector_correction.core.gcp_manager import (
    GcpManager,
    NotEnoughGcpsException,
    TransformCreationException
)
from vector_correction.gui.draw_line_tool import DrawLineTool
from vector_correction.gui.corrections_dock import CorrectionsDockWidget

VERSION = '0.0.1'


class VectorCorrectionPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        super().__init__()
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QgsApplication.locale()
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            '{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.toolbar = None
        self.draw_correction_action = None
        self.map_tool = None
        self.temp_layer = None
        self.show_gcps_action = None
        self.apply_correction_action = None
        self.actions = []
        self.dock = None

        self.gcp_manager = GcpManager(self.iface.mapCanvas())

    @staticmethod
    def tr(message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('VectorCorrection', message)

    def initProcessing(self):
        """Create the Processing provider"""

    def initGui(self):
        """Creates application GUI widgets"""
        self.initProcessing()

        self.dock = CorrectionsDockWidget(self.gcp_manager)

        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.setUserVisible(False)

        self.toolbar = QToolBar(self.tr('Vector Correction Toolbar'))
        self.toolbar.setObjectName('vectorCorrectionToolbar')
        self.iface.addToolBar(self.toolbar)

        self.draw_correction_action = QAction(self.tr('Draw Correction'), parent=self.toolbar)
        self.toolbar.addAction(self.draw_correction_action)
        self.draw_correction_action.triggered.connect(self.draw_correction)
        self.actions.append(self.draw_correction_action)

        self.show_gcps_action = QAction(self.tr('Show GCPS'), parent=self.toolbar)
        self.toolbar.addAction(self.show_gcps_action)
        self.actions.append(self.show_gcps_action)
        self.dock.setToggleVisibilityAction(self.show_gcps_action)

        self.apply_correction_action = QAction(self.tr('Apply Correction'), parent=self.toolbar)
        self.toolbar.addAction(self.apply_correction_action)
        self.apply_correction_action.triggered.connect(self.apply_correction)
        self.actions.append(self.apply_correction_action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.gcp_manager.clear()

        for a in self.actions:
            a.deleteLater()
        self.actions = []

        if self.toolbar is not None:
            self.toolbar.deleteLater()
            self.toolbar = None
        if self.map_tool is not None:
            self.map_tool.deleteLater()
            self.map_tool = None
        if self.temp_layer is not None:
            self.temp_layer.deleteLater()
            self.temp_layer = None
        if self.dock is not None:
            self.dock.deleteLater()
            self.dock = None

    def draw_correction(self):
        """
        Triggers the draw correction map tool
        """

        layer_options = QgsVectorLayer.LayerOptions(QgsProject.instance().transformContext())
        layer_options.skipCrsValidation = True
        self.temp_layer = QgsVectorLayer('LineString', 'f', 'memory', layer_options)
        self.temp_layer.setCrs(QgsCoordinateReferenceSystem())
        self.temp_layer.startEditing()
        self.map_tool = DrawLineTool(map_canvas=self.iface.mapCanvas(),
                                     cad_dock_widget=self.iface.cadDockWidget(),
                                     message_bar=self.iface.messageBar())
        self.map_tool.setLayer(self.temp_layer)
        self.map_tool.digitizingCompleted.connect(self._correction_added)
        self.iface.mapCanvas().setMapTool(self.map_tool)

    def _correction_added(self, feature: QgsFeature):
        """
        Triggered when a new correction line is digitized
        """
        digitize_line = feature.geometry()
        self.gcp_manager.add_gcp(origin=QgsPointXY(digitize_line.constGet().startPoint()),
                                 destination=QgsPointXY(digitize_line.constGet().endPoint()),
                                 crs=self.iface.mapCanvas().mapSettings().destinationCrs())

    def apply_correction(self):
        """
        Applies the defined corrections to visible features
        """
        target_layer = self.iface.activeLayer()
        layer_crs = target_layer.crs()

        canvas_extent = self.iface.mapCanvas().mapSettings().visibleExtent()
        canvas_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        # we need to transform the canvas extent to the layer crs in order to filter features
        canvas_to_layer_transform = QgsCoordinateTransform(canvas_crs,
                                                           layer_crs,
                                                           QgsProject.instance().transformContext())
        layer_filter_rect = canvas_to_layer_transform.transformBoundingBox(canvas_extent)

        request = QgsFeatureRequest()
        request.setFilterRect(layer_filter_rect)
        request.setNoAttributes()

        features = target_layer.getFeatures(request)
        feature_map = {
            f.id(): f.geometry()
            for f in features
        }

        target_layer.beginEditCommand(self.tr('Correct features'))

        try:
            transformed_features = self.gcp_manager.transform_features(
                features=feature_map,
                feature_crs=layer_crs,
                extent=canvas_extent,
                extent_crs=canvas_crs)
        except NotEnoughGcpsException as e:
            self.iface.messageBar().pushCritical('', str(e))
            return
        except TransformCreationException as e:
            self.iface.messageBar().pushCritical('', str(e))
            return

        if any(g.isNull() for g in transformed_features.values()):
            self.iface.messageBar().pushCritical('', self.tr('One or more features failed to transform'))
            return

        for _id, geometry in transformed_features.items():
            target_layer.changeGeometry(_id, geometry, True)

        target_layer.endEditCommand()
        target_layer.triggerRepaint()
