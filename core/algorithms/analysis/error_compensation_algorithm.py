# -*- codin# -*- coding: utf-8 -*-
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

import os
from typing import Optional

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QgsFeatureSink,
                       QgsProcessing,
                       QgsProcessingParameterField,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBoolean,
                       QgsProcessingMultiStepFeedback)

from ..algorithm_runner import AlgorithmRunner
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...constants import QGIS_TOC_GROUPS
from ...services.layer_service import LayerService
from ...services.system_service import SystemService
from ....gui.settings.options_settings_dlg import OptionsSettingsPage


class ErrorCompensationProcessingAlgorithm(QgsProcessingAlgorithm):
    T1_80_RASTER = 'T1_80_RASTER'
    T1_ERROR_RASTER = 'T1_ERROR_RASTER'
    T2_80_RASTER = 'T2_80_RASTER'
    T2_ERROR_RASTER = 'T2_ERROR_RASTER'
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
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.T1_80_RASTER,
                self.tr('T1 80% raster'),
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.T1_ERROR_RASTER,
                self.tr('T1 error raster'),
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.T2_80_RASTER,
                self.tr('T2 80% raster'),
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.T2_ERROR_RASTER,
                self.tr('T2 error raster'),
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.POINTS, self.tr("Export final surface points")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        t180Raster = self.parameterAsRasterLayer(parameters, self.T1_80_RASTER, context)
        t1ErrorRaster = self.parameterAsRasterLayer(parameters, self.T1_ERROR_RASTER, context)
        t280Raster = self.parameterAsRasterLayer(parameters, self.T2_80_RASTER, context)
        t2ErrorRaster = self.parameterAsRasterLayer(parameters, self.T2_ERROR_RASTER, context)
        exportPoints = self.parameterAsBool(parameters, self.POINTS, context)

        filePath = self.project.homePath()
        t1FilePath = os.path.join(filePath, '03_Error_Compensation', 'T1_Error_Compensation', 'T1_Final_Surface.tiff')
        t2FilePath = os.path.join(filePath, '03_Error_Compensation', 'T2_Error_Compensation', 'T2_Final_Surface.tiff')
        t1Expression = f'"{t180Raster.name()}@1" + "{t1ErrorRaster.name()}@1"'
        t2Expression = f'"{t280Raster.name()}@1" + "{t2ErrorRaster.name()}@1"'
        t1Parameters = self.getRasterCalculatorParameters(t1Expression, t180Raster, t1FilePath)
        t2Parameters = self.getRasterCalculatorParameters(t2Expression, t280Raster, t2FilePath)

        for parameter in [t1Parameters, t2Parameters]:

            finalSurface = self.algRunner.runRasterCalculator(parameter, context=context, feedback=feedback)

            if exportPoints:
                rasterName = finalSurface.name().split('_')
                surfacePointsName = f"{rasterName[0]}_{rasterName[1]}_Points.shp"
                surfacePointsPath = os.path.join(filePath, '03_Error_Compensation', surfacePointsName)
                surfacePointsParameters = self.getYieldPointsParameters(finalSurface, 'yield', surfacePointsPath)

                finalSurfacePoints = self.algRunner.runPixelsToPoints(surfacePointsParameters,
                                                                      context=context, feedback=feedback)
                self.layerService.addMapLayer(finalSurfacePoints, QGIS_TOC_GROUPS[5])

            self.layerService.addMapLayer(finalSurface, QGIS_TOC_GROUPS[5])

        return {self.OUTPUT: None}

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

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'calculateerrorcompensation'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Calculate Error Compensation')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Analysis')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'analysis'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return ProcessingAlgorithmHelpCreator.shortHelpString(self.name())

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('ErrorCompensationProcessingAlgorithm', string)

    def createInstance(self):
        return ErrorCompensationProcessingAlgorithm()
