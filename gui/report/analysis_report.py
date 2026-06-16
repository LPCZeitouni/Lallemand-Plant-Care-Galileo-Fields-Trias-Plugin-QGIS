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
import os.path

from qgis.PyQt.QtCore import QObject

from ...core.algorithms.algorithm_runner import AlgorithmRunner
from ...core.services.layer_service import LayerService
from ...core.services.message_service import MessageService


class AnalysisReport(QObject):

    def __init__(self, project):
        """Constructor."""
        super(AnalysisReport, self).__init__()
        self.project = project
        self.filePath = self.project.homePath()
        self.outputPath = os.path.normpath(os.path.join(self.filePath, '05_Results'))
        self.layerService = LayerService()
        self.messageService = MessageService()
        self.algRunner = AlgorithmRunner()

    def verifyLoadedLayer(self, layerName):
        layer = self.project.mapLayersByName(layerName)
        if not layer:
            self.messageService.warningMessage('Filtering points', f'There is no {layerName} layer loaded!')
        return layer

    def getFields(self, layer, fieldNames):
        return self.layerService.filterByFieldName(layer, fieldNames, inverse=False)

    def getRasterLayers(self, filterString):
        layers = self.project.mapLayers().values()
        rasterLayer = self.layerService.filterByLayerName(list(layers), filterString, inverse=True)

        if rasterLayer:
            return rasterLayer
        else:
            self.messageService.warningMessage('Sampling validation', f'There is no kriging raster layer loaded!')

    def runCreateReport(self):
        gainPointsLayer = self.verifyLoadedLayer('Gain_Points')
        t1TotalLayer = self.verifyLoadedLayer('T1_total')
        t2TotalLayer = self.verifyLoadedLayer('T2_total')
        t1FinalLayer = self.verifyLoadedLayer('T1_Final_Points')
        t2FinalLayer = self.verifyLoadedLayer('T2_Final_Points')
        t1t2Layer = self.verifyLoadedLayer('T1_T2_total')

        parameters = {
            'GAIN_POINTS': gainPointsLayer[0],
            'OUTPUT': self.outputPath,
            'T1_LAYER': t1TotalLayer[0],
            'T1_SURFACE': t1FinalLayer[0],
            'T2_LAYER': t2TotalLayer[0],
            'T2_SURFACE': t2FinalLayer[0],
            'TRIAL_NAME': '',
            'YIELD': t1t2Layer[0]
        }
        self.algRunner.runCreateReport(parameters)

    def runCreatePresentation(self):
        gainPointsLayer = self.verifyLoadedLayer('Gain_Points')
        t1ValidationLayer = self.verifyLoadedLayer('T1_validation')
        t2ValidationLayer = self.verifyLoadedLayer('T2_validation')
        t1SurfaceLayer = self.verifyLoadedLayer('T1_Final_Points')
        t2SurfaceLayer = self.verifyLoadedLayer('T2_Final_Points')

        parameters = {
            'GAIN_POINTS': gainPointsLayer[0],
            'OUTPUT': self.outputPath,
            'T1_SURFACE': t1SurfaceLayer[0],
            'T1_VALIDATION': t1ValidationLayer[0],
            'T2_SURFACE': t2SurfaceLayer[0],
            'T2_VALIDATION': t2ValidationLayer[0],
            'TRIAL_NAME': '',
            'YIELD_FIELD': 'yield'
        }
        self.algRunner.runCreatePresentation(parameters)
