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


from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject, QgsFeatureIterator,
                       QgsProcessing,
                       QgsProcessingParameterField,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingException,
                       QgsFeatureSink,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSink)

from ..algorithm_runner import AlgorithmRunner
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...constants import VALIDATION_FIELDS
from ...services.layer_service import LayerService
from ...services.system_service import SystemService


class SamplingProcessingAlgorithm(QgsProcessingAlgorithm):
    TREATMENT_FILTERED_LAYER = 'TREATMENT_FILTERED_LAYER'
    SAMPLE_VALUE = 'SAMPLE_VALUE'
    COMPLEMENTARY_VALUE = 'COMPLEMENTARY_VALUE'
    SAMPLE_OUTPUT = 'SAMPLE_OUTPUT'
    COMPLEMENTARY_OUTPUT = 'COMPLEMENTARY_OUTPUT'

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
                self.TREATMENT_FILTERED_LAYER,
                self.tr('Treatment points Layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SAMPLE_VALUE,
                self.tr('Sample percentage'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=None,
                optional=False, minValue=0.0, maxValue=100)
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.COMPLEMENTARY_VALUE,
                self.tr('Complementary percentage'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=None,
                optional=False, minValue=0.0, maxValue=100)
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.SAMPLE_OUTPUT,
                self.tr('Treatment sample output layer')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.COMPLEMENTARY_OUTPUT,
                self.tr('Treatment complementary output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        treatmentLayer = self.parameterAsVectorLayer(parameters, self.TREATMENT_FILTERED_LAYER, context)
        sample = self.parameterAsInt(parameters, self.SAMPLE_VALUE, context)
        complement = self.parameterAsInt(parameters, self.COMPLEMENTARY_VALUE, context)
        (sampleSink, sampleDestinationId) = self.parameterAsSink(parameters, self.SAMPLE_OUTPUT,
                                                                 context, treatmentLayer.fields(),
                                                                 treatmentLayer.wkbType(),
                                                                 treatmentLayer.sourceCrs())
        (complementSink, complementDestinationId) = self.parameterAsSink(parameters, self.COMPLEMENTARY_OUTPUT,
                                                                         context, treatmentLayer.fields(),
                                                                         treatmentLayer.wkbType(),
                                                                         treatmentLayer.sourceCrs())

        if sample + complement > 100:
            raise QgsProcessingException('The sum of percentages cannot be bigger than 100!')
        elif sample + complement < 100:
            raise QgsProcessingException('The sum of percentages cannot be less than 100!')

        layers = self.project.mapLayers().values()
        for layer in layers:
            if layer.name() in ['T1_80_perc', 'T2_80_perc', 'T1_validation', 'T2_validation']:

                raise QgsProcessingException(
                    f'The layer {layer.name()} is already loaded! Unload the layer and run again.'
                )

            else:

                multiFeedback = QgsProcessingMultiStepFeedback(3, feedback)
                multiFeedback.pushInfo(self.tr(f'Sampling features from {treatmentLayer.name()}...\n'))

                sampleFeatures, complementaryFeatures = self.layerService.getPercentualFeaturesById(treatmentLayer, sample, featureList=True)

                multiFeedback.pushInfo(self.tr(f'{len(sampleFeatures)} features for principal sample.\n'))
                self.addToSink(sampleFeatures, sampleSink, feedback)

                multiFeedback.pushInfo(self.tr(f'{len(complementaryFeatures)} features for complementary sample.\n'))
                self.addToSink(complementaryFeatures, complementSink, feedback)

                return {self.SAMPLE_OUTPUT: sampleDestinationId, self.COMPLEMENTARY_OUTPUT: complementDestinationId}

    @staticmethod
    def addToSink(features, sink, feedback):

        totalFeatures = len(features)
        total = 100.0 / totalFeatures if totalFeatures else 0

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break

            sink.addFeature(feature, QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'simplerandomsampling'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Simple random sampling')

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
        return QCoreApplication.translate('SamplingProcessingAlgorithm', string)

    def createInstance(self):
        return SamplingProcessingAlgorithm()
