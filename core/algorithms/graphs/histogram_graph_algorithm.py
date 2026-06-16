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
QgsProcessingParameterFile,
                       QgsProcessingParameterField,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingMultiStepFeedback)

from ..algorithm_runner import AlgorithmRunner
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...constants import QGIS_TOC_GROUPS
from ...services.layer_service import LayerService
from ...services.plot_service import PlotterService
from ...services.system_service import SystemService
from ....gui.settings.options_settings_dlg import OptionsSettingsPage


class HistogramGraphProcessingAlgorithm(QgsProcessingAlgorithm):
    YIELD_LAYER = 'YIELD_FILTERED_LAYER'
    YIELD_FIELD = 'YIELD_FIELD'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.project = QgsProject.instance()
        self.layerService = LayerService()
        self.algRunner = AlgorithmRunner()
        self.plotterService = PlotterService()
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
                self.YIELD_LAYER,
                self.tr('Layer to calculate statistics'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.YIELD_FIELD,
                self.tr('Field with histogram values'),
                parentLayerParameterName=self.YIELD_LAYER,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.OUTPUT,
                self.tr('Output folder'),
                QgsProcessingParameterFile.Folder
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        yieldLayer = self.parameterAsVectorLayer(parameters, self.YIELD_LAYER, context)
        yieldField = self.parameterAsFields(parameters, self.YIELD_FIELD, context)
        outputFolder = self.parameterAsFile(parameters, self.OUTPUT, context)

        filePath = self.project.homePath()
        multiFeedback = QgsProcessingMultiStepFeedback(3, feedback)
        multiFeedback.pushInfo(self.tr(f'Collecting data...\n'))

        histogramValues = [feature[yieldField[0]] for feature in yieldLayer.getFeatures()]
        dataTable = self.getHistogramParameters(yieldLayer, yieldField[0])

        multiFeedback.pushInfo(self.tr(f'Drawing histograms...\n'))
        self.plotterService.createFrequencyHistogram(histogramValues, dataTable,
                                                     yieldLayer.name(), exportPng=True, path=outputFolder)
        self.plotterService.createVFrequencyHistogram(histogramValues, dataTable,
                                                      yieldLayer.name(), exportPng=True, path=outputFolder)

        return {self.OUTPUT: None}

    @staticmethod
    def addToSink(features, sink, feedback):
        total = 100.0 / len(features) if len(features) else 0

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break

            sink.addFeature(feature, QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))

    def getHistogramParameters(self, layer, field):
        statisticFields = ['COUNT', 'MIN', 'MAX', 'SUM', 'MEAN', 'STD_DEV', 'CV']
        statisticValues = self.algRunner.runBasicStatisticsForFields(layer, field)
        tableData = list()

        for statistic in statisticFields:
            if statistic == 'COUNT':
                tableData.append([f'{float(statisticValues[statistic]):.0f}'])
            else:
                tableData.append([f'{float(statisticValues[statistic]):.2f}'])

        return tableData

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'histogramfromattribute'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Histogram graph from attribute')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Graphs')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'graphs'

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
        return QCoreApplication.translate('HistogramGraphProcessingAlgorithm', string)

    def createInstance(self):
        return HistogramGraphProcessingAlgorithm()
