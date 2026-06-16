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
from qgis.PyQt.QtCore import QObject

from ..settings.options_settings_dlg import OptionsSettingsPage
from ...core.algorithms.algorithm_runner import AlgorithmRunner
from ...core.services.layer_service import LayerService
from ...core.services.message_service import MessageService


class FilteringHarvesterPoints(QObject):

    def __init__(self, project):
        """Constructor."""
        super(FilteringHarvesterPoints, self).__init__()
        self.project = project
        self.settings = OptionsSettingsPage().getTreatmentPolygonsSettings()
        self.kriging = OptionsSettingsPage().getKrigingSettings()
        self.layerService = LayerService()
        self.messageService = MessageService()
        self.algRunner = AlgorithmRunner()

    def runHarvesterFilter(self):

        harvesterLayers = self.getHarvesterLayers()

        treatmentPolygon = self.verifyLoadedLayer('GPS_points_treatment')
        contour = self.verifyLoadedLayer('GPS_points_contour')

        reproject: bool() = None

        idFields = self.getFields(harvesterLayers[0], ['id', 'fid', 'OBJECTID', 'Obj__Id', 'Id', 'ID'])
        yieldField = self.getFields(harvesterLayers[0], self.kriging[0].split(';'))

        if harvesterLayers[0].crs().isGeographic():
            reproject = True

        parameters = {
            'HARVESTER_POINTS_LAYER': harvesterLayers[0],
            'REPROJECT': reproject,
            'ID_FIELD': idFields[0].name(),
            'YIELD_FIELD': None,
            'TREATMENT_POLYGONS': treatmentPolygon[0],
            'TREATMENT_ID_FIELD': 'Num',
            'BOUNDARY_POLYGON': contour[0],
            'TARGET_PROJECTION': 0, 'DATE_COLUMN': 0}

        self.algRunner.runHarvesterFilter(parameters)

    def getFields(self, layer, fieldNames):
        return self.layerService.filterByFieldName(layer, fieldNames, inverse=False)

    def getHarvesterLayers(self):
        layers = self.project.mapLayers().values()
        harvesterLayer = self.layerService.filterByLayerName(list(layers),
                                                             ['1_Krig_', 'GPS', 'T1', 'T2', 'Gain'],
                                                             inverse=False)
        if harvesterLayer:
            return sorted(harvesterLayer, key=lambda x: x.name())
        else:
            self.messageService.warningMessage('Filtering points', f'There is no harvester layer loaded!')

    def verifyLoadedLayer(self, layerName):
        layer = self.project.mapLayersByName(layerName)
        if not layer:
            self.messageService.warningMessage('Filtering points', f'There is no {layerName} layer loaded!')
        return layer
