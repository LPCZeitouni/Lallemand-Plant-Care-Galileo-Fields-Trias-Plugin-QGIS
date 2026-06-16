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
                       QgsProcessingMultiStepFeedback)

from ..algorithm_runner import AlgorithmRunner
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...constants import QGIS_TOC_GROUPS
from ...services.layer_service import LayerService
from ...services.system_service import SystemService
from ....gui.settings.options_settings_dlg import OptionsSettingsPage


class CreateSampleLayersProcessingAlgorithm(QgsProcessingAlgorithm):
    YIELD_FILTERED_LAYER = 'YIELD_FILTERED_LAYER'
    TREATMENT_FIELD = 'TREATMENT_FIELD'
    YIELD_FIELD = 'YIELD_FIELD'
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
            QgsProcessingParameterVectorLayer(
                self.YIELD_FILTERED_LAYER,
                self.tr('Yield filtered layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.TREATMENT_FIELD,
                self.tr('Field with treatment information'),
                parentLayerParameterName=self.YIELD_FILTERED_LAYER,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.YIELD_FIELD,
                self.tr('Yield field'),
                parentLayerParameterName=self.YIELD_FILTERED_LAYER,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        yieldLayer = self.parameterAsVectorLayer(parameters, self.YIELD_FILTERED_LAYER, context)
        treatmentField = self.parameterAsFields(parameters, self.TREATMENT_FIELD, context)
        yieldField = self.parameterAsFields(parameters, self.YIELD_FIELD, context)

        filePath = self.project.homePath()
        histogramPath = os.path.join(filePath, '05_Results', '01_Histograms')
        multiFeedback = QgsProcessingMultiStepFeedback(3, feedback)
        multiFeedback.pushInfo(self.tr(f'Initializing filtering...\n'))

        treatmentsDict = self.algRunner.runFilterTreatments(yieldLayer, treatmentField[0], 'TEMPORARY_OUTPUT', 'TEMPORARY_OUTPUT', context, feedback)

        for name, layer in treatmentsDict.items():
            treatmentPath = str()
            treatment = str()
            if name == 'T1_OUTPUT':
                treatment = 'T1'
                treatmentPath = os.path.join(filePath, '00_Data', '02_Sampling', f'{treatment}_total.shp')
            elif name == 'T2_OUTPUT':
                treatment = 'T2'
                treatmentPath = os.path.join(filePath, '00_Data', '02_Sampling', f'{treatment}_total.shp')

            self.layerService.saveVectorLayer(layer, treatmentPath)
            totalLayer = self.layerService.loadShapeFile(QGIS_TOC_GROUPS[2], treatmentPath)
            self.layerService.applySymbology(totalLayer, yieldField[0])
            self.algRunner.runHistogramFromAttribute(totalLayer, yieldField[0], histogramPath, context, feedback)

            sampleDict = self.algRunner.runSimpleSample(layer, context, feedback)

            for key, sampleLayer in sampleDict.items():
                group = QGIS_TOC_GROUPS[2] if key == 'SAMPLE_OUTPUT' else QGIS_TOC_GROUPS[4]
                treatmentSuffix = '80_perc' if key == 'SAMPLE_OUTPUT' else 'validation'
                middlePath = os.path.join('00_Data', '02_Sampling') if key == 'SAMPLE_OUTPUT' else '02_Validation'
                samplePath = os.path.join(filePath, middlePath, f'{treatment}_{treatmentSuffix}.shp')

                if key == 'SAMPLE_OUTPUT':
                    self.layerService.saveVectorLayer(sampleLayer, samplePath)
                    percentualLayer = self.layerService.loadShapeFile(group, samplePath)
                    self.algRunner.runHistogramFromAttribute(percentualLayer, yieldField[0], histogramPath, context,
                                                             feedback)
                    self.layerService.applySymbology(percentualLayer, yieldField[0])
                else:
                    validationLayer = self.layerService.createValidationVectorLayer(sampleLayer, yieldField[0])
                    self.layerService.saveVectorLayer(validationLayer, samplePath)
                    self.layerService.loadShapeFile(group, samplePath)

        return {self.OUTPUT: None}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'createsamplelayers'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Create sample layers')

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
        return QCoreApplication.translate('CreateSampleLayersProcessingAlgorithm', string)

    def createInstance(self):
        return CreateSampleLayersProcessingAlgorithm()
