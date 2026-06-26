# -*- coding: utf-8 -*-
"""
/***************************************************************************
A QGIS plugin for agronomic field trial analysis based on geostatistical (Kriging-based) models.
/***************************************************************************
Begin        : 2026-02-09
Copyright    : (C) 2026 Olivier Cor
Email        : ocor@lallemand.com
License      : GNU General Public License v3.0 or later (GPLv3+)
/***************************************************************************
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
/***************************************************************************
You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
/***************************************************************************
"""

from qgis.PyQt.QtCore import QObject

from ..settings.options_settings_dlg import OptionsSettingsPage
from ...core.algorithms.algorithm_runner import AlgorithmRunner
from ...core.services.layer_service import LayerService
from ...core.services.message_service import MessageService


class SamplingLayersValidation(QObject):

    def __init__(self, project):
        """Constructor."""
        super(SamplingLayersValidation, self).__init__()
        self.project = project
        self.layerService = LayerService()
        self.messageService = MessageService()
        self.algRunner = AlgorithmRunner()
        self.kriging = OptionsSettingsPage().getKrigingSettings()
        self.layers = self.project.instance().mapLayers()

    def verifyLoadedLayer(self, layerName):
        layer = self.project.mapLayersByName(layerName)[0]
        if not layer:
            self.messageService.warningMessage('Filtering points', f'There is no {layerName} layer loaded!')
            return None
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

    def runCalculateError(self):
        t1ValidationLayer = self.verifyLoadedLayer('T1_validation')
        t2ValidationLayer = self.verifyLoadedLayer('T2_validation')
        t1Field = self.getFields(t1ValidationLayer, self.kriging[0].split(';'))
        t2Field = self.getFields(t2ValidationLayer, self.kriging[0].split(';'))

        t1Raster = self.getRasterLayers(['1_Krig_T1_80_perc_'])
        t2Raster = self.getRasterLayers(['1_Krig_T2_80_perc_'])

        parameters = {
            'T1_RASTER': t1Raster[0],
            'T1_VALIDATION_LAYER': t1ValidationLayer,
            'T1_VALIDATION_FIELD': None,
            'T2_RASTER': t2Raster[0],
            'T2_VALIDATION_LAYER': t2ValidationLayer,
            'T2_VALIDATION_FIELD': None
        }

        self.algRunner.runCalculateError(parameters)

    def runErrorCompensation(self):
        t1Raster = self.getRasterLayers(['1_Krig_T1_80_perc_'])
        t2Raster = self.getRasterLayers(['1_Krig_T2_80_perc_'])
        t1ErrorRaster = self.getRasterLayers(['1_Krig_T1_validation_error_'])
        t2ErrorRaster = self.getRasterLayers(['1_Krig_T2_validation_error_'])

        parameters = {
            'POINTS': True,
            'T1_80_RASTER': t1Raster[0],
            'T1_ERROR_RASTER': t1ErrorRaster[0],
            'T2_80_RASTER': t2Raster[0],
            'T2_ERROR_RASTER': t2ErrorRaster[0]
        }
        self.algRunner.runErrorCompensation(parameters)

    def runGainSurface(self):
        t1Raster = self.getRasterLayers(['T1_Final_Surface'])
        t2Raster = self.getRasterLayers(['T2_Final_Surface'])
        parameters = {
            'POINTS': True,
            'T1_RASTER': t1Raster[0],
            'T2_RASTER': t2Raster[0]
        }
        self.algRunner.runGainSurface(parameters)

    def runCreateSampleLayersParameters(self):
        yieldLayer = self.verifyLoadedLayer('T1_T2_total')
        treatmentField = self.getFields(yieldLayer, ['Traitement'])
        yieldField = self.getFields(yieldLayer, self.kriging[0].split(';'))

        parameters = {
            'YIELD_FILTERED_LAYER': yieldLayer,
            'TREATMENT_FIELD': treatmentField[0].name(),
            'YIELD_FIELD': None,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }

        self.algRunner.runCreateSampleLayers(parameters)
