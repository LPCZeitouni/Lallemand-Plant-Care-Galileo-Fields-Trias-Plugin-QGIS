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
                       QgsProcessingParameterFeatureSink,
                       QgsProcessing,
                       QgsProcessingParameterField,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterEnum,
QgsProcessingParameterBoolean,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingMultiStepFeedback)

from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ....gui.settings.options_settings_dlg import OptionsSettingsPage
from ..algorithm_runner import AlgorithmRunner
from ...constants import VALIDATION_FIELDS, QGIS_TOC_GROUPS
from ...services.layer_service import LayerService
from ...services.system_service import SystemService


class FilterTreatmentProcessingAlgorithm(QgsProcessingAlgorithm):
    YIELD_FILTERED_LAYER = 'YIELD_FILTERED_LAYER'
    TREATMENT_FIELD = 'TREATMENT_FIELD'
    TREATMENT_NAMES = 'TREATMENT_NAMES'
    T1_OUTPUT = 'T1_OUTPUT'
    T2_OUTPUT = 'T2_OUTPUT'

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
            QgsProcessingParameterVectorLayer(
                self.YIELD_FILTERED_LAYER,
                self.tr('Yield layer (T1 and T2)'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.TREATMENT_FIELD,
                self.tr('Field to evaluate'),
                parentLayerParameterName=self.YIELD_FILTERED_LAYER,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )
        self.treatmentList = self.treatmentSettings.getTreatmentPolygonsSettings()
        self.addParameter(
            QgsProcessingParameterEnum(
                self.TREATMENT_NAMES,
                self.tr('Treatment names'),
                options=[treatment for treatment in self.treatmentList[0]],
                allowMultiple=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.T1_OUTPUT,
                self.tr('T1 layer output folder')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.T2_OUTPUT,
                self.tr('T2 layer output folder')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        yieldLayer = self.parameterAsVectorLayer(parameters, self.YIELD_FILTERED_LAYER, context)
        treatmentField = self.parameterAsFields(parameters, self.TREATMENT_FIELD, context)
        treatmentIndex = self.parameterAsEnums(parameters, self.TREATMENT_NAMES, context)

        (t1Sink, t1DestinationId) = self.parameterAsSink(parameters, self.T1_OUTPUT,
                                                         context, yieldLayer.fields(),
                                                         yieldLayer.wkbType(),
                                                         yieldLayer.sourceCrs())
        (t2Sink, t2DestinationId) = self.parameterAsSink(parameters, self.T2_OUTPUT,
                                                         context, yieldLayer.fields(),
                                                         yieldLayer.wkbType(),
                                                         yieldLayer.sourceCrs())

        multiFeedback = QgsProcessingMultiStepFeedback(3, feedback)
        multiFeedback.pushInfo(self.tr(f'Getting treatments...'))

        treatments = zip(treatmentIndex, self.treatmentList[0])

        for treatmentIndex, treatmentName in treatments:

            request = f"\"{treatmentField[0]}\"='{treatmentName}'"

            multiFeedback.pushInfo(self.tr(f'Selecting features from {treatmentName}...'))

            selectedFeatures = self.layerService.getFeaturesByRequest(yieldLayer, request, featureList=True)

            multiFeedback.pushInfo(self.tr(f'{len(selectedFeatures)} features from {treatmentName}.\n'))

            if treatmentName == 'T1':
                self.addToSink(selectedFeatures, t1Sink, feedback)
            else:
                self.addToSink(selectedFeatures, t2Sink, feedback)

        return {self.T1_OUTPUT: t1DestinationId, self.T2_OUTPUT: t2DestinationId}

    @staticmethod
    def addToSink(features, sink, feedback):
        total = 100.0 / len(features) if len(features) else 0

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
        return 'filtertreatments'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Filter treatments')

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
        return QCoreApplication.translate('FilterTreatmentProcessingAlgorithm', string)

    def createInstance(self):
        return FilterTreatmentProcessingAlgorithm()
