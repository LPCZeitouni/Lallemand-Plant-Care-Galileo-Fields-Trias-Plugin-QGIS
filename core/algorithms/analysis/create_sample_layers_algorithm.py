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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
---------------------------------------------------------------------
"""

import os
from typing import Optional

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProject,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterEnum,
    QgsProcessingMultiStepFeedback
)

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
    CONTROL_TREATMENT = 'CONTROL_TREATMENT'
    OUTPUT = 'OUTPUT'

    PROJECT_CONTROL_VARIABLE = "galileo_control_treatment"

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
        Define inputs for creating sample and validation layers.
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

        self.addParameter(
            QgsProcessingParameterEnum(
                self.CONTROL_TREATMENT,
                self.tr('Control treatment for final surface comparison'),
                options=['T1', 'T2'],
                defaultValue=0,
                optional=False
            )
        )

    def storeControlTreatment(self, controlTreatment):
        """
        Store the selected control treatment at QGIS project level.

        This value will be reused later during final surface symbology
        harmonisation and report generation.
        """

        variables = QgsProject.instance().customVariables()
        variables[self.PROJECT_CONTROL_VARIABLE] = controlTreatment
        QgsProject.instance().setCustomVariables(variables)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Create T1/T2 total, sample and validation layers.
        """

        yieldLayer = self.parameterAsVectorLayer(parameters, self.YIELD_FILTERED_LAYER, context)
        treatmentField = self.parameterAsFields(parameters, self.TREATMENT_FIELD, context)
        yieldField = self.parameterAsFields(parameters, self.YIELD_FIELD, context)

        controlIndex = self.parameterAsEnum(parameters, self.CONTROL_TREATMENT, context)
        controlTreatment = ['T1', 'T2'][controlIndex]
        self.storeControlTreatment(controlTreatment)

        filePath = self.project.homePath()
        histogramPath = os.path.join(filePath, '05_Results', '01_Histograms')

        multiFeedback = QgsProcessingMultiStepFeedback(3, feedback)
        multiFeedback.pushInfo(self.tr('Initializing filtering...\n'))
        multiFeedback.pushInfo(
            self.tr(f'Control treatment selected for final surface comparison: {controlTreatment}\n')
        )

        treatmentsDict = self.algRunner.runFilterTreatments(
            yieldLayer,
            treatmentField[0],
            'TEMPORARY_OUTPUT',
            'TEMPORARY_OUTPUT',
            context,
            feedback
        )

        for name, layer in treatmentsDict.items():
            treatmentPath = str()
            treatment = str()

            if name == 'T1_OUTPUT':
                treatment = 'T1'
                treatmentPath = os.path.join(
                    filePath,
                    '00_Data',
                    '02_Sampling',
                    f'{treatment}_total.shp'
                )

            elif name == 'T2_OUTPUT':
                treatment = 'T2'
                treatmentPath = os.path.join(
                    filePath,
                    '00_Data',
                    '02_Sampling',
                    f'{treatment}_total.shp'
                )

            self.layerService.saveVectorLayer(layer, treatmentPath)
            totalLayer = self.layerService.loadShapeFile(QGIS_TOC_GROUPS[2], treatmentPath)
            self.layerService.applySymbology(totalLayer, yieldField[0])

            self.algRunner.runHistogramFromAttribute(
                totalLayer,
                yieldField[0],
                histogramPath,
                context,
                feedback
            )

            sampleDict = self.algRunner.runSimpleSample(layer, context, feedback)

            for key, sampleLayer in sampleDict.items():

                group = QGIS_TOC_GROUPS[2] if key == 'SAMPLE_OUTPUT' else QGIS_TOC_GROUPS[4]
                treatmentSuffix = '80_perc' if key == 'SAMPLE_OUTPUT' else 'validation'
                middlePath = os.path.join('00_Data', '02_Sampling') if key == 'SAMPLE_OUTPUT' else '02_Validation'

                samplePath = os.path.join(
                    filePath,
                    middlePath,
                    f'{treatment}_{treatmentSuffix}.shp'
                )

                if key == 'SAMPLE_OUTPUT':
                    self.layerService.saveVectorLayer(sampleLayer, samplePath)
                    percentualLayer = self.layerService.loadShapeFile(group, samplePath)

                    self.algRunner.runHistogramFromAttribute(
                        percentualLayer,
                        yieldField[0],
                        histogramPath,
                        context,
                        feedback
                    )

                    self.layerService.applySymbology(percentualLayer, yieldField[0])

                else:
                    validationLayer = self.layerService.createValidationVectorLayer(
                        sampleLayer,
                        yieldField[0]
                    )

                    self.layerService.saveVectorLayer(validationLayer, samplePath)
                    self.layerService.loadShapeFile(group, samplePath)

        return {self.OUTPUT: None}

    def name(self):
        return 'createsamplelayers'

    def displayName(self):
        return self.tr('Create sample layers')

    def group(self):
        return self.tr('Analysis')

    def groupId(self):
        return 'analysis'

    def shortHelpString(self):
        return ProcessingAlgorithmHelpCreator.shortHelpString(self.name())

    def tr(self, string):
        return QCoreApplication.translate(
            'CreateSampleLayersProcessingAlgorithm',
            string
        )

    def createInstance(self):
        return CreateSampleLayersProcessingAlgorithm()
