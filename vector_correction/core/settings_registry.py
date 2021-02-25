# -*- coding: utf-8 -*-
"""Settings registry

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2020 by Nyall Dawson'
__date__ = '29/10/2020'
__copyright__ = 'Copyright 2020, North Road'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.analysis import (
    QgsGcpTransformerInterface
)
from qgis.core import (
    QgsSettings,
    QgsLineSymbol,
    QgsSimpleLineSymbolLayer,
    QgsMarkerLineSymbolLayer,
    QgsEllipseSymbolLayer,
    QgsMarkerSymbol
)


class SettingsRegistry:
    """
    Plugin settings registry
    """

    ARROW_SYMBOL = None

    @staticmethod
    def transform_method() -> QgsGcpTransformerInterface.TransformMethod:
        """
        Returns the current transform method
        """
        settings = QgsSettings()
        current_method = QgsGcpTransformerInterface.TransformMethod(
            settings.value('vector_corrections/method',
                           int(QgsGcpTransformerInterface.TransformMethod.Helmert),
                           int, QgsSettings.Plugins)
        )
        return current_method

    @staticmethod
    def set_transform_method(method: QgsGcpTransformerInterface.TransformMethod):
        """
        Sets the current transform method
        """
        settings = QgsSettings()
        settings.setValue('vector_corrections/method', int(method), QgsSettings.Plugins)

    @staticmethod
    def default_arrow_symbol() -> QgsLineSymbol:
        """
        Returns the default arrow symbol to use for GCP lines
        """
        symbol = QgsLineSymbol([])
        simple_line = QgsSimpleLineSymbolLayer.create(
            {'align_dash_pattern': '0', 'capstyle': 'flat', 'customdash': '5;2',
             'customdash_map_unit_scale': '3x:0,0,0,0,0,0', 'customdash_unit': 'MM', 'dash_pattern_offset': '0',
             'dash_pattern_offset_map_unit_scale': '3x:0,0,0,0,0,0', 'dash_pattern_offset_unit': 'MM',
             'draw_inside_polygon': '0', 'joinstyle': 'round', 'line_color': '255,170,0,255', 'line_style': 'solid',
             'line_width': '1', 'line_width_unit': 'Point', 'offset': '0', 'offset_map_unit_scale': '3x:0,0,0,0,0,0',
             'offset_unit': 'Point', 'ring_filter': '0', 'tweak_dash_pattern_on_corners': '0', 'use_custom_dash': '0',
             'width_map_unit_scale': '3x:0,0,0,0,0,0'}
        )
        symbol.changeSymbolLayer(0, simple_line)

        arrow_marker = QgsMarkerLineSymbolLayer.create(
            {'average_angle_length': '4', 'average_angle_map_unit_scale': '3x:0,0,0,0,0,0', 'average_angle_unit': 'MM',
             'interval': '3', 'interval_map_unit_scale': '3x:0,0,0,0,0,0', 'interval_unit': 'MM', 'offset': '0',
             'offset_along_line': '0.8', 'offset_along_line_map_unit_scale': '3x:0,0,0,0,0,0',
             'offset_along_line_unit': 'MM', 'offset_map_unit_scale': '3x:0,0,0,0,0,0', 'offset_unit': 'MM',
             'placement': 'lastvertex', 'ring_filter': '0', 'rotate': '1'}
        )

        triangle = QgsEllipseSymbolLayer.create(
            {'angle': '270', 'color': '255,170,0,255', 'horizontal_anchor_point': '1', 'joinstyle': 'miter',
             'offset': '0,0', 'offset_map_unit_scale': '3x:0,0,0,0,0,0', 'offset_unit': 'Point',
             'outline_color': '255,170,0,255', 'outline_style': 'no', 'outline_width': '0',
             'outline_width_map_unit_scale': '3x:0,0,0,0,0,0', 'outline_width_unit': 'MM', 'size': '7',
             'size_map_unit_scale': '3x:0,0,0,0,0,0', 'size_unit': 'MM', 'symbol_height': '5',
             'symbol_height_map_unit_scale': '3x:0,0,0,0,0,0', 'symbol_height_unit': 'Point', 'symbol_name': 'triangle',
             'symbol_width': '7', 'symbol_width_map_unit_scale': '3x:0,0,0,0,0,0', 'symbol_width_unit': 'Point',
             'vertical_anchor_point': '1'})
        triangle_symbol = QgsMarkerSymbol([])
        triangle_symbol.changeSymbolLayer(0, triangle)
        arrow_marker.setSubSymbol(triangle_symbol)

        symbol.appendSymbolLayer(arrow_marker)

        return symbol

    @staticmethod
    def arrow_symbol() -> QgsLineSymbol:
        """
        Returns the arrow symbol to use for lines
        """
        if SettingsRegistry.ARROW_SYMBOL is not None:
            return SettingsRegistry.ARROW_SYMBOL.clone()

        SettingsRegistry.ARROW_SYMBOL = SettingsRegistry.default_arrow_symbol()
        return SettingsRegistry.ARROW_SYMBOL.clone()

    @staticmethod
    def set_arrow_symbol(symbol: QgsLineSymbol):
        """
        Sets the arrow symbol to use for lines
        """
        SettingsRegistry.ARROW_SYMBOL = symbol.clone()


SETTINGS_REGISTRY = SettingsRegistry()
