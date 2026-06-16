# -*- cod# -*- coding: utf-8 -*-
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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsProcessingParameterField,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer)


from ..algorithm_runner import AlgorithmRunner
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...constants import VALIDATION_FIELDS
from ...services.layer_service import LayerService
from ...services.system_service import SystemService


class CalculateErrorProcessingAlgorithm(QgsProcessingAlgorithm):
    T1_RASTER = 'T1_RASTER'
    T2_RASTER = 'T2_RASTER'
    T1_VALIDATION_LAYER = 'T1_VALIDATION_LAYER'
    T2_VALIDATION_LAYER = 'T2_VALIDATION_LAYER'
    T1_VALIDATION_FIELD = 'T1_VALIDATION_FIELD'
    T2_VALIDATION_FIELD = 'T2_VALIDATION_FIELD'
    T1_OUTPUT = 'T1_OUTPUT'
    T2_OUTPUT = 'T2_OUTPUT'

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
            QgsProcessingParameterRasterLayer(
                self.T1_RASTER,
                self.tr('T1 Kriging Raster'),
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T1_VALIDATION_LAYER,
                self.tr('T1 validation Points Layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.T1_VALIDATION_FIELD,
                self.tr('T1 field to evaluate'),
                parentLayerParameterName=self.T1_VALIDATION_LAYER,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.T2_RASTER,
                self.tr('T2 Kriging Raster'),
                [QgsProcessing.TypeRaster]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T2_VALIDATION_LAYER,
                self.tr('T2 Validation Points Layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.T2_VALIDATION_FIELD,
                self.tr('T2 Field to evaluate'),
                parentLayerParameterName=self.T2_VALIDATION_LAYER,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                self.T1_OUTPUT,
                self.tr("Original layer without empty geometries")
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                self.T2_OUTPUT,
                self.tr("Original layer without empty geometries")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        t1Raster = self.parameterAsRasterLayer(parameters, self.T1_RASTER, context)
        t2Raster = self.parameterAsRasterLayer(parameters, self.T2_RASTER, context)
        t1ValidationLayer = self.parameterAsVectorLayer(parameters, self.T1_VALIDATION_LAYER, context)
        t2ValidationLayer = self.parameterAsVectorLayer(parameters, self.T2_VALIDATION_LAYER, context)
        t1ValidationField = self.parameterAsFields(parameters, self.T1_VALIDATION_FIELD, context)
        t2ValidationField = self.parameterAsFields(parameters, self.T2_VALIDATION_FIELD, context)

        parameters = self.getParameters(t1Raster, t1ValidationLayer, t1ValidationField, t2Raster, t2ValidationLayer, t2ValidationField)

        outputList = list()

        for raster, values in parameters.items():

            output = self.algRunner.runAddRasterValuesToPoints(values[1], [values[0]], context=context, feedback=feedback)
            estimatedField = self.systemService.getFieldName(values[0].name())

            layerWithErrorValues = self.layerService.updateFeatures(output, values[2][0], estimatedField, feedback)

            rmse = self.algRunner.runRMSE(layerWithErrorValues, values[2][0], VALIDATION_FIELDS[2], context=context, feedback=feedback)

            layerWithRmse = self.layerService.updateRmseField(layerWithErrorValues, estimatedField, rmse['OUTPUT']['RMSE'], rmse['OUTPUT']['PERCENTUAL_RMSE'], feedback)

            fieldsToDelete = self.layerService.filterByFieldName(layerWithRmse, [estimatedField], inverse=False)
            layerWithCleanFields = self.layerService.deleteFields(layerWithRmse, fieldsToDelete)

            self.layerService.updateOutputLayer(values[1], layerWithCleanFields)

            outputList.append(layerWithCleanFields)

        return {self.T1_OUTPUT: outputList[0], self.T2_OUTPUT: outputList[1]}

    @staticmethod
    def getParameters(t1Raster, t1ValidationLayer, t1ValidationField, t2Raster, t2ValidationLayer, t2ValidationField):
        return {
            'T1': [t1Raster, t1ValidationLayer, t1ValidationField],
            'T2': [t2Raster, t2ValidationLayer, t2ValidationField]
                }

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'calculateerror'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Calculate square error')

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
        return QCoreApplication.translate('CalculateErrorProcessingAlgorithm', string)

    def createInstance(self):
        return CalculateErrorProcessingAlgorithm()