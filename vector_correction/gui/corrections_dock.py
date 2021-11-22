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

from qgis.PyQt import uic
from qgis.PyQt.QtCore import (
    pyqtSignal,
    QDir
)
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QAction,
    QFileDialog
)
from qgis.analysis import (
    QgsGcpTransformerInterface
)
from qgis.core import (
    QgsSymbol,
    QgsVectorFileWriter,
    QgsProviderRegistry,
    QgsVectorLayer,
    QgsProject,
    QgsFileUtils,
    QgsApplication
)
from qgis.gui import (
    QgsPanelWidget,
    QgsDockWidget,
    QgsPanelWidgetStack
)

from vector_correction.core.gcp_manager import GcpManager
from vector_correction.core.settings_registry import SettingsRegistry
from vector_correction.gui.gui_utils import GuiUtils

WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('point_list.ui'))


class PointListWidget(QgsPanelWidget, WIDGET):
    """
    A table for gcp lists
    """

    extent_symbol_changed = pyqtSignal()

    def __init__(self, gcp_manager: GcpManager, parent: QWidget = None):
        super().__init__(parent)

        self.setupUi(self)

        self.gcp_manager = gcp_manager
        self.table_view.setModel(self.gcp_manager)

        self.delete_rows_action = QAction(self.tr('Delete Selected Rows'), self)
        self.delete_rows_action.setIcon(QgsApplication.getThemeIcon('mActionDeleteSelectedFeatures.svg'))
        self.delete_rows_action.triggered.connect(self._delete_selected)
        self.toolbar.addAction(self.delete_rows_action)
        self.delete_rows_action.setEnabled(False)

        self.toolbar.addSeparator()

        self.save_action = QAction(self.tr('Save'), self)
        self.save_action.setToolTip(self.tr('Save GCPs to file'))
        self.save_action.setIcon(QgsApplication.getThemeIcon('mActionFileSave.svg'))
        self.save_action.triggered.connect(self._save)
        self.toolbar.addAction(self.save_action)

        self.load_action = QAction(self.tr('Load'), self)
        self.load_action.setToolTip(self.tr('Loads GCPs from file'))
        self.load_action.setIcon(QgsApplication.getThemeIcon('mActionFileOpen.svg'))
        self.load_action.triggered.connect(self._load)
        self.toolbar.addAction(self.load_action)

        self.export_action = QAction(self.tr('Export'), self)
        self.export_action.setToolTip(self.tr('Exports correction vectors to a line layer'))
        self.export_action.setIcon(QgsApplication.getThemeIcon('mIconLineLayer.svg'))
        self.export_action.triggered.connect(self._export)
        self.toolbar.addAction(self.export_action)

        self.toolbar.addSeparator()

        self.settings_action = QAction(self.tr('Settings'), self)
        self.settings_action.setIcon(QgsApplication.getThemeIcon('/propertyicons/settings.svg'))
        self.settings_action.triggered.connect(self._show_settings)
        self.toolbar.addAction(self.settings_action)

        self.settings_panel = None

        self.table_view.selectionModel().selectionChanged.connect(self._selection_changed)

    def _show_settings(self):
        """
        Shows the settings panel
        """
        self.settings_panel = SettingsWidget(self.gcp_manager)
        self.settings_panel.panelAccepted.connect(self._update_settings)
        self.settings_panel.extent_symbol_changed.connect(self.extent_symbol_changed)
        self.settings_panel.transform_method_changed.connect(self._transform_method_changed)
        self.openPanel(self.settings_panel)

    def _update_settings(self):
        """
        Updates the stored settings
        """
        self.settings_panel.deleteLater()
        self.settings_panel = None

    def _selection_changed(self):
        """
        Triggered when table selection is changed
        """
        self.delete_rows_action.setEnabled(bool(self.table_view.selectionModel().selectedIndexes()))

    def _delete_selected(self):
        """
        Deletes selected rows from the table
        """
        rows = []
        for index in self.table_view.selectionModel().selectedIndexes():
            if index.row() not in rows:
                rows.append(index.row())

        self.gcp_manager.remove_rows(rows)

    def _transform_method_changed(self):
        """
        Triggered when the selected transform method is changed
        """
        self.gcp_manager.update_residuals()

    def _export(self):
        """
        Exports GCP corrections to a line layer
        """
        file_filter = QgsVectorFileWriter.fileFilterString()
        dest, selected_filter = QFileDialog.getSaveFileName(self, self.tr('Destination File'), QDir.homePath(),
                                                            file_filter)
        if not dest:
            return
        dest = QgsFileUtils.ensureFileNameHasExtension(dest, QgsFileUtils.extensionsFromFilter(selected_filter))

        new_filename, new_layer, error = self.gcp_manager.export_to_layer(dest)
        if not error:
            source = QgsProviderRegistry.instance().encodeUri('ogr', {'path': new_filename, 'layerName': new_layer})
            vl = QgsVectorLayer(source, self.tr('Corrections'))
            QgsProject.instance().addMapLayer(vl)

    def _save(self):
        """
        Saves GCPs to disk
        """
        dest, _ = QFileDialog.getSaveFileName(self, self.tr('Destination File'), QDir.homePath(),
                                              self.tr('TXT files (*.txt)'))
        if not dest:
            return

        dest = QgsFileUtils.ensureFileNameHasExtension(dest, ['txt'])
        self.gcp_manager.save_to_file(dest)

    def _load(self):
        """
        Loads GCPs from disk
        """
        src, _ = QFileDialog.getOpenFileName(self, self.tr('Destination File'), QDir.homePath(),
                                             self.tr('TXT files (*.txt)'))
        if not src:
            return

        self.gcp_manager.load_from_file(src)


SETTINGS_WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('settings.ui'))


class SettingsWidget(QgsPanelWidget, SETTINGS_WIDGET):
    """
    A table for gcp lists
    """

    extent_symbol_changed = pyqtSignal()
    transform_method_changed = pyqtSignal()

    def __init__(self, gcp_manager: GcpManager, parent: QWidget = None):
        super().__init__(parent)

        self.gcp_manager = gcp_manager

        self.setupUi(self)

        self.setPanelTitle(self.tr('Settings'))

        for method in [QgsGcpTransformerInterface.TransformMethod.Linear,
                       QgsGcpTransformerInterface.TransformMethod.Helmert,
                       QgsGcpTransformerInterface.TransformMethod.PolynomialOrder1,
                       QgsGcpTransformerInterface.TransformMethod.PolynomialOrder2,
                       QgsGcpTransformerInterface.TransformMethod.PolynomialOrder3,
                       QgsGcpTransformerInterface.TransformMethod.ThinPlateSpline,
                       QgsGcpTransformerInterface.TransformMethod.Projective
                       ]:
            self.combo_method.addItem(QgsGcpTransformerInterface.methodToString(method), int(method))

        self.arrow_style_button.setSymbolType(QgsSymbol.Line)
        self.extent_style_button.setSymbolType(QgsSymbol.Fill)
        self.restore_settings()

        self.arrow_style_button.changed.connect(self._symbol_changed)
        self.extent_style_button.changed.connect(self._extent_symbol_changed)
        self.combo_method.currentIndexChanged[int].connect(self._method_changed)

        self.preview_color_button.setAllowOpacity(True)
        self.preview_color_button.setColor(SettingsRegistry.preview_color())
        self.preview_color_button.colorChanged.connect(self._preview_color_changed)

    def restore_settings(self):
        """
        Restores saved settings
        """
        current_method = SettingsRegistry.transform_method()
        self.combo_method.setCurrentIndex(self.combo_method.findData(int(current_method)))

        self.arrow_style_button.setSymbol(SettingsRegistry.arrow_symbol())
        self.extent_style_button.setSymbol(SettingsRegistry.extent_symbol())

    def _symbol_changed(self):
        """
        Called when the line symbol type is changed
        """
        SettingsRegistry.set_arrow_symbol(self.arrow_style_button.symbol())
        self.gcp_manager.update_line_symbols()

    def _extent_symbol_changed(self):
        """
        Called when the extent symbol type is changed
        """
        SettingsRegistry.set_extent_symbol(self.extent_style_button.symbol())
        self.extent_symbol_changed.emit()

    def _method_changed(self, _: int):
        """
        Called when the method combobox value is changed
        """
        SettingsRegistry.set_transform_method(
            QgsGcpTransformerInterface.TransformMethod(
                int(self.combo_method.currentData())
            )
        )
        self.transform_method_changed.emit()

    def _preview_color_changed(self):
        """
        Called when the feature preview color is changed
        """
        SettingsRegistry.set_preview_color(self.preview_color_button.color())


class CorrectionsDockWidget(QgsDockWidget):
    """
    A dock widget container for plugin GUI components
    """

    extent_symbol_changed = pyqtSignal()

    def __init__(self, gcp_manager: GcpManager, parent=None):
        super().__init__(parent)

        self.gcp_manager = gcp_manager

        self.setObjectName('CorrectionsDockWidget')
        self.setWindowTitle(self.tr('Vector Corrections'))

        self.stack = QgsPanelWidgetStack()

        w = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.stack)
        w.setLayout(layout)
        self.setWidget(w)

        self.table_widget = PointListWidget(self.gcp_manager)
        self.table_widget.setDockMode(True)
        self.stack.setMainPanel(self.table_widget)
        self.table_widget.extent_symbol_changed.connect(self.extent_symbol_changed)
