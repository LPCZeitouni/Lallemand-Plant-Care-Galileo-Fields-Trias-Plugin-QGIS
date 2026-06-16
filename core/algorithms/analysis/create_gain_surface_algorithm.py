# -*- coding: utf-8 -*-
"""
/***************************************************************************
A QGIS plugin for agronomic field trial analysis based on geostatistical (Kriging-based) models.
/***************************************************************************
Begin        : 2026-02-09
Copyright    : (C) 2026 Olivier Cor
Email        : ocor@lallemand.com
License      : GNU General Public Licens/***************************************************************************e v3.0 or later (GPLv3+)
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
/***************************************************************************
"""


import os
from typing import Optional
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBoolean)

from ..algorithm_runner import AlgorithmRunner
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...constants import QGIS_TOC_GROUPS
from ...services.layer_service import LayerService
from ...services.system_service import SystemService
from ....gui.settings.options_settings_dlg import OptionsSettingsPage


class GainSurfaceProcessingAlgorithm(QgsProcessingAlgorithm):
    T1_RASTER = 'T1_RASTER' # Référence (Témoin)
    T2_RASTER = 'T2_RASTER' # Traitement
    POINTS = 'POINTS'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.project = QgsProject.instance()
        self.layerService = LayerService()
        self.algRunner = AlgorithmRunner()
        self.systemService = SystemService()
        self.treatmentSettings = OptionsSettingsPage()
        self.treatmentList: Optional[list] = None

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.T1_RASTER,
                self.tr('Minuend final surface (Reference T1)'),
                [QgsProcessing.TypeRaster]
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.T2_RASTER,
                self.tr('Subtrahend final surface (Treatment T2)'),
                [QgsProcessing.TypeRaster]
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.POINTS, self.tr("Export gain points")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        minuendRaster = self.parameterAsRasterLayer(parameters, self.T1_RASTER, context)
        subtrahendRaster = self.parameterAsRasterLayer(parameters, self.T2_RASTER, context)
        exportPoints = self.parameterAsBool(parameters, self.POINTS, context)

        filePath = self.project.homePath()
        
        # --- CONFIGURATION DES CLASSES ET COULEURS ---
        # Bornes : <0 (Gris), 0-5 (Jaune), 5-15 (Vert clair), >15 (Vert foncé)
        thresholds = [0, 5, 15]
        colors = ['#808080', '#FFFF00', '#90EE90', '#006400']
        
        # --- CALCUL DU POURCENTAGE ---
        m_name = minuendRaster.name()
        s_name = subtrahendRaster.name()
        
        gainSurfaceDir = os.path.join(filePath, '04_Gain_Surface')
        if not os.path.exists(gainSurfaceDir):
            os.makedirs(gainSurfaceDir)
            
        GainSurfacePath = os.path.join(gainSurfaceDir, 'Yield_Gain.tiff')
        
        # Expression : (T2 - T1) / T1 * 100
        Expression = f'if("{m_name}@1" <= 0, 0, (("{s_name}@1" - "{m_name}@1") / "{m_name}@1") * 100)'
        
        calcParam = self.getRasterCalculatorParameters(Expression, minuendRaster, GainSurfacePath)
        GainSurface = self.algRunner.runRasterCalculator(calcParam, context=context, feedback=feedback)
        
        # Application de la symbologie fixe via le service
        self.layerService.applyGainSymbology(GainSurface, thresholds, colors)
        self.layerService.addMapLayer(GainSurface, QGIS_TOC_GROUPS[6])

        # --- EXPORT DES POINTS (si coché) ---
        if exportPoints:
            pointsPath = os.path.join(gainSurfaceDir, 'Gain_Points.shp')
            pointsParameters = self.getYieldPointsParameters(GainSurface, 'yield', pointsPath)
            gainPoints = self.algRunner.runPixelsToPoints(pointsParameters, context=context, feedback=feedback)

            # Histogramme avec les mêmes couleurs et bornes
            resultsDir = os.path.join(filePath, '05_Results')
            if not os.path.exists(resultsDir):
                os.makedirs(resultsDir)
                
            yieldGainHistogramPath = os.path.join(resultsDir, 'Yield_Gain_Histogram.png')
            
            # Appel au service pour générer l'histogramme coloré
            self.layerService.yieldGainFrequencyHistogram(
                gainPoints, 
                yieldGainHistogramPath, 
                thresholds=thresholds, 
                colors=colors
            )

            self.layerService.addMapLayer(gainPoints, QGIS_TOC_GROUPS[6])

        return {self.OUTPUT: GainSurfacePath}

    @staticmethod
    def getRasterCalculatorParameters(expression, layer, filePath):
        return {'EXPRESSION': expression,
                'LAYERS': [layer],
                'CELLSIZE': 0,
                'EXTENT': None,
                'CRS': layer.crs().authid(),
                'OUTPUT': filePath}

    @staticmethod
    def getYieldPointsParameters(gainSurface, fieldName, filePath):
        return {
            'INPUT_RASTER': gainSurface,
            'RASTER_BAND': 1,
            'FIELD_NAME': fieldName,
            'OUTPUT': filePath
        }

    def name(self): return 'creategainsurface'
    def displayName(self): return self.tr('Create Gain Surface')
    def group(self): return self.tr('Analysis')
    def groupId(self): return 'analysis'
    def shortHelpString(self): return ProcessingAlgorithmHelpCreator.shortHelpString(self.name())
    def tr(self, string): return QCoreApplication.translate('GainSurfaceProcessingAlgorithm', string)
    def createInstance(self): return GainSurfaceProcessingAlgorithm()
