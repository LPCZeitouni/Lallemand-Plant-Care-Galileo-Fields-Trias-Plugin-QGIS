# -*- coding: utf-8 -*-
"""
LallemandGeostatFieldTrialTreatments

A QGIS plugin for agronomic field trial analysis using geostatistical
(Kriging-based) models to analyze and compare treatment scenarios.

---------------------------------------------------------------------
Begin        : 2026-02-09
Copyright    : (C) 2026 Olivier Cor
Email        : ocor@lallemand.com
License      : GNU General Public License v3.0 or later (GPLv3+)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
---------------------------------------------------------------------
"""
from processing.gui.wrappers import WidgetWrapper
from qgis.core import (QgsProject, QgsMapLayerProxyModel, QgsProcessingParameterDefinition)
from qgsmaplayercombobox import QgsMapLayerComboBox

from ...core.services.layer_service import LayerService


class FilteredLayerWidgetWrapper(WidgetWrapper):
    def __init__(self, *args, **kwargs):
        super(FilteredLayerWidgetWrapper, self).__init__(*args, **kwargs)

    def createWidget(self):
        layerService = LayerService()
        self.gpsLayerComboBox = QgsMapLayerComboBox()
        layers = QgsProject.instance().mapLayers()
        # treatmentLayer = layerService.filterByLayerName(list(layers.values()), ['T1', 'T2', 'Gain', 'Yield'], inverse=True)
        treatmentLayer = layerService.filterExactLayerName(list(layers.values()), ['GPS_points'], inverse=False)
        self.gpsLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.gpsLayerComboBox.setExceptedLayerList(treatmentLayer)
        return self.gpsLayerComboBox

    def parentLayerChanged(self, layer=None):
        pass

    def setLayer(self, layer):
        self.gpsLayerComboBox.setLayer(layer)

    def setValue(self, value):
        pass

    def value(self):
        return self.gpsLayerComboBox.currentLayer()

    def postInitialize(self, wrappers):
        pass


class ParameterFilteredLayer(QgsProcessingParameterDefinition):
    def __init__(self, name, description="", optional=False):
        super().__init__(name, description, optional)

    def clone(self):
        copy = ParameterFilteredLayer(self.name(), self.description())
        return copy

    def type(self):
        return self.typeName()

    @staticmethod
    def typeName():
        return "filteredlayer"

    def checkValueIsAcceptable(self, value, context=None):
        return True

    def metadata(self):
        return {
            "widget_wrapper": "lallemand_plant_care.gui.wrappers.filtered_layer_wrapper.FilteredLayerWidgetWrapper"
        }

    def valueAsPythonString(self, value, context):
        return str(value)

    def asScriptCode(self):
        raise NotImplementedError()

    @classmethod
    def fromScriptCode(cls, name, description, isOptional, definition):
        raise NotImplementedError()
