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
from typing import Optional

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
    QgsCoordinateTransform,
    QgsReferencedRectangle
)
from qgis.gui import (
    QgisInterface
)

from vector_correction.core.gcp_manager import (
    GcpManager,
    NotEnoughGcpsException,
    TransformCreationException
)
from vector_correction.gui.corrections_dock import CorrectionsDockWidget
from vector_correction.gui.draw_extent_tool import (
    DrawExtentTool,
    DrawExtentToolHandler
)
from vector_correction.gui.draw_line_tool import (
    DrawLineTool,
    DrawLineToolHandler
)
from vector_correction.gui.gui_utils import GuiUtils

VERSION = '0.0.2'


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
        self.aoi_tool = None
        self.aoi_tool_handler = None
        self.map_tool = None
        self.map_tool_handler = None
        self.temp_layer = None
        self.draw_aoi_action = None
        self.show_aoi_action = None
        self.show_gcps_action = None
        self.apply_correction_action = None
        self.actions = []
        self.dock = None

        self.aoi: Optional[QgsReferencedRectangle] = None
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

        self.draw_aoi_action = QAction(self.tr('Draw AOI'), parent=self.toolbar)
        self.draw_aoi_action.setIcon(GuiUtils.get_icon('draw_extent.svg'))
        self.toolbar.addAction(self.draw_aoi_action)
        self.actions.append(self.draw_aoi_action)

        self.show_aoi_action = QAction(self.tr('Show AOI'), parent=self.toolbar)
        self.show_aoi_action.setIcon(GuiUtils.get_icon('show_extent.svg'))
        self.show_aoi_action.setCheckable(True)
        self.show_aoi_action.setChecked(False)
        self.show_aoi_action.setEnabled(False)
        self.toolbar.addAction(self.show_aoi_action)
        self.show_aoi_action.toggled.connect(self.show_aoi)
        self.actions.append(self.show_aoi_action)

        self.aoi_tool = DrawExtentTool(map_canvas=self.iface.mapCanvas(),
                                       message_bar=self.iface.messageBar())
        self.aoi_tool_handler = DrawExtentToolHandler(self.aoi_tool, self.draw_aoi_action)
        self.iface.registerMapToolHandler(self.aoi_tool_handler)
        self.aoi_tool.extent_set.connect(self.set_aoi)

        self.draw_correction_action = QAction(self.tr('Draw Correction'), parent=self.toolbar)
        self.draw_correction_action.setIcon(GuiUtils.get_icon('draw_correction.svg'))
        self.toolbar.addAction(self.draw_correction_action)
        self.actions.append(self.draw_correction_action)

        self.show_gcps_action = QAction(self.tr('Show GCPS'), parent=self.toolbar)
        self.show_gcps_action.setIcon(GuiUtils.get_icon('gcp_table.svg'))
        self.toolbar.addAction(self.show_gcps_action)
        self.actions.append(self.show_gcps_action)
        self.dock.setToggleVisibilityAction(self.show_gcps_action)

        self.apply_correction_action = QAction(self.tr('Apply Correction'), parent=self.toolbar)
        self.apply_correction_action.setIcon(GuiUtils.get_icon('apply_corrections.svg'))
        self.toolbar.addAction(self.apply_correction_action)
        self.apply_correction_action.triggered.connect(self.apply_correction)
        self.actions.append(self.apply_correction_action)
        self.apply_correction_action.setEnabled(False)

        self.map_tool = DrawLineTool(map_canvas=self.iface.mapCanvas(),
                                     cad_dock_widget=self.iface.cadDockWidget(),
                                     message_bar=self.iface.messageBar())
        self.map_tool_handler = DrawLineToolHandler(self.map_tool, self.draw_correction_action)
        self.iface.registerMapToolHandler(self.map_tool_handler)

        layer_options = QgsVectorLayer.LayerOptions(QgsProject.instance().transformContext())
        layer_options.skipCrsValidation = True
        self.temp_layer = QgsVectorLayer('LineString', 'f', 'memory', layer_options)
        self.temp_layer.setCrs(QgsCoordinateReferenceSystem())
        self.temp_layer.startEditing()

        self.map_tool.setLayer(self.temp_layer)

        self.map_tool.digitizingCompleted.connect(self._correction_added)

        self.dock.extent_symbol_changed.connect(self.aoi_tool.update_fill_symbol)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.gcp_manager.clear()

        self.iface.unregisterMapToolHandler(self.aoi_tool_handler)
        self.iface.unregisterMapToolHandler(self.map_tool_handler)

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
        Applies the defined corrections to visible features in all editable layers
        """
        for _, layer in QgsProject.instance().mapLayers().items():
            if isinstance(layer, QgsVectorLayer) and layer.isEditable():
                if not self.apply_correction_to_layer(layer):
                    break

    def apply_correction_to_layer(self, target_layer: QgsVectorLayer) -> bool:
        """
        Applies the defined corrections to visible features
        """
        if not self.aoi:
            return False

        layer_crs = target_layer.crs()

        # we need to transform the AOI extent to the layer crs in order to filter features
        aoi_to_layer_transform = QgsCoordinateTransform(self.aoi.crs(),
                                                        layer_crs,
                                                        QgsProject.instance().transformContext())
        layer_filter_rect = aoi_to_layer_transform.transformBoundingBox(self.aoi)

        request = QgsFeatureRequest()
        request.setFilterRect(layer_filter_rect)
        request.setNoAttributes()

        features = target_layer.getFeatures(request)
        feature_map = {
            f.id(): f.geometry()
            for f in features
        }

        try:
            transformed_features = self.gcp_manager.transform_features(
                features=feature_map,
                feature_crs=layer_crs,
                extent=self.aoi,
                extent_crs=self.aoi.crs())
        except NotEnoughGcpsException as e:
            self.iface.messageBar().pushCritical('', str(e))
            return False
        except TransformCreationException as e:
            self.iface.messageBar().pushCritical('', str(e))
            return False

        if any(g.isNull() for g in transformed_features.values()):
            self.iface.messageBar().pushCritical('', self.tr('One or more features failed to transform'))
            return False

        target_layer.beginEditCommand(self.tr('Correct features'))

        for _id, geometry in transformed_features.items():
            target_layer.changeGeometry(_id, geometry, True)

        target_layer.endEditCommand()
        target_layer.triggerRepaint()
        return True

    def set_aoi(self, aoi: QgsReferencedRectangle):
        """
        Sets the current area of interest
        :param aoi: area of interest
        """
        self.show_aoi_action.setEnabled(True)
        self.apply_correction_action.setEnabled(True)
        self.aoi = aoi

        self.show_aoi_action.setChecked(True)

    def show_aoi(self, visible: bool):
        """
        Shows (or hides) the current area of interest
        """
        self.aoi_tool.show_aoi(visible)
