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


class TreatmentPolygons(QObject):

    def __init__(self, project):
        """Constructor."""
        super(TreatmentPolygons, self).__init__()
        self.project = project
        self.layerService = LayerService()
        self.messageService = MessageService()
        self.algRunner = AlgorithmRunner()
        self.settings = OptionsSettingsPage().getTreatmentPolygonsSettings()

    def verifyLoadedLayer(self, layerName):
        layer = self.project.mapLayersByName(layerName)[0]
        if not layer:
            self.messageService.warningMessage('Filtering points', f'There is no {layerName} layer loaded!')
            return None
        return layer

    def runTreatmentPolygons(self):
        reproject: bool() = None
        epsg: str = ''
        method = 1 if self.settings[4][1] else 0
        layer = self.verifyLoadedLayer('GPS_points')

        if layer and layer.crs().isGeographic():
            crsOperations = self.layerService.getSuggestedCrs(layer)
            reproject = True
            epsg = crsOperations[2]

        parameters = {'GPS_POINTS_LAYER': layer,
                      'REPROJECT': reproject,
                      'CRS': '',
                      'SORTING_FIELD': 'ID',
                      'METHOD': method,
                      'BORDER_SIZE': float(self.settings[3]),
                      'BOUNDARY': True}

        self.algRunner.runTreatmentPolygons(epsg, parameters)
