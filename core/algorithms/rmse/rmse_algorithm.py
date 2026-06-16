# -*- coding: utf-8# -*- coding: utf-8 -*-
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
import math

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsProcessingParameterField,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer)

from ..algorithm_runner import AlgorithmRunner
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...services.layer_service import LayerService
from ...services.system_service import SystemService


class RMSEProcessingAlgorithm(QgsProcessingAlgorithm):

    VALIDATION_LAYER = 'VALIDATION_LAYER'
    VALIDATION_FIELD = 'YIELD_FIELD'
    ERROR_FIELD = 'ERROR_FIELD'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.project = QgsProject.instance()
        self.layerService = LayerService()
        self.algRunner = AlgorithmRunner()
        self.systemService = SystemService()

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.VALIDATION_LAYER,
                self.tr('Validation points layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.VALIDATION_FIELD,
                self.tr('Field to evaluate'),
                parentLayerParameterName=self.VALIDATION_LAYER,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.ERROR_FIELD,
                self.tr('Field with square error'),
                parentLayerParameterName=self.VALIDATION_LAYER,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        validationLayer = self.parameterAsVectorLayer(parameters, self.VALIDATION_LAYER, context)
        validationField = self.parameterAsFields(parameters, self.VALIDATION_FIELD, context)
        errorField = self.parameterAsFields(parameters, self.ERROR_FIELD, context)

        errorStatistics = self.algRunner.runBasicStatisticsForFields(validationLayer,
                                                                     errorField[0],
                                                                     context=context,
                                                                     feedback=feedback)
        variableStatistics = self.algRunner.runBasicStatisticsForFields(validationLayer,
                                                                        validationField[0],
                                                                        context=context,
                                                                        feedback=feedback)
        rmse = math.sqrt(errorStatistics['SUM'] / errorStatistics['COUNT'])
        percentualRmse = (rmse / (variableStatistics['SUM'] / variableStatistics['COUNT'])) * 100

        return {self.OUTPUT: {'RMSE': rmse, 'PERCENTUAL_RMSE': percentualRmse}}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'rmse'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('RMSE')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Statistics')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'statistics'

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
        return QCoreApplication.translate('RMSEProcessingAlgorithm', string)

    def createInstance(self):
        return RMSEProcessingAlgorithm()
