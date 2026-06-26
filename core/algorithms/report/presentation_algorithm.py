# -*-# -*- coding: utf-8 -*-
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

import os.path

from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt import QtWidgets
from qgis.PyQt.Qt import QVariant
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsProcessingParameterField,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterDefinition)

from ....gui.wrappers.trial_name_wrapper import ParameterTrialName
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...constants import FETCH_ALL_TRIAL, FETCH_ONE_TRIAL, DIRECTORY_STRUCTURE
from ...factories.postgres_factory import PostgresFactory
from ...factories.sqlite_factory import SqliteFactory
from ...services.plot_service import PlotterService
from ...services.report_service import ReportService
from ...services.statistics_service import StatisticsService
from ...services.system_service import SystemService


class PresentationProcessingAlgorithm(QgsProcessingAlgorithm):

    TRIAL_NAME = 'TRIAL_NAME'
    T1_SURFACE = 'T1_SURFACE'
    T2_SURFACE = 'T2_SURFACE'
    YIELD_FIELD = 'YIELD_FIELD'
    T1_VALIDATION = 'T1_VALIDATION'
    T2_VALIDATION = 'T2_VALIDATION'
    GAIN_POINTS = 'GAIN_POINTS'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.project = QgsProject.instance()
        self.databaseFactory = SqliteFactory()
        self.plotService = PlotterService()
        self.reportService = ReportService()
        self.systemService = SystemService()
        self.statisticsService = StatisticsService()

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.addParameter(
            ParameterTrialName(
                self.TRIAL_NAME,
                description="Trial name"
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T1_SURFACE,
                self.tr('T1 surface points layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T2_SURFACE,
                self.tr('T2 surface points layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.YIELD_FIELD,
                self.tr('Yield field'),
                parentLayerParameterName=self.T1_SURFACE,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T1_VALIDATION,
                self.tr('T1 validation layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T2_VALIDATION,
                self.tr('T2 validation layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.GAIN_POINTS,
                self.tr('Gain points layer'),
                [QgsProcessing.TypeVectorPoint],
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

    @staticmethod
    def parameterAsTrial(parameters, name, context):
        return parameters[name]

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        trialId = self.parameterAsTrial(parameters, self.TRIAL_NAME, context)
        t1SurfaceLayer = self.parameterAsVectorLayer(parameters, self.T1_SURFACE, context)
        t2SurfaceLayer = self.parameterAsVectorLayer(parameters, self.T2_SURFACE, context)
        yieldField = self.parameterAsFields(parameters, self.YIELD_FIELD, context)
        t1ValidationLayer = self.parameterAsVectorLayer(parameters, self.T1_VALIDATION, context)
        t2ValidationLayer = self.parameterAsVectorLayer(parameters, self.T2_VALIDATION, context)
        gainLayer = self.parameterAsVectorLayer(parameters, self.GAIN_POINTS, context)
        outputFolder = self.parameterAsFile(parameters, self.OUTPUT, context)

        resultFolder = list(DIRECTORY_STRUCTURE.keys())[5]
        rootPath = os.path.join(self.project.homePath(), resultFolder)

        pValue, anovaStats = self.getAnovaStatistics(t1SurfaceLayer, t2SurfaceLayer, yieldField[0])
        gainStats = self.getGainStatistics(gainLayer, yieldField[0])
        self.plotService.createGainStatisticsTable(pValue, gainStats, anovaStats, True, rootPath)
        presentationData = self.getPresentationParameters(trialId, t1ValidationLayer, t2ValidationLayer, rootPath)

        self.reportService.createPresentation(presentationData, outputFolder)

        return {self.OUTPUT: None}

    def getGainStatistics(self, gainLayer, field):
        gainStatsList = list()
        gainStats = self.statisticsService.getGainStatistics(gainLayer, field)
        for statistic in gainStats:
            gainStatsList.append([f'{statistic:.2f}'])
        return gainStatsList

    def getAnovaStatistics(self, t1SurfaceLayer, t2SurfaceLayer, field):
        anovaStatsList = list()
        fValue, pValue = self.statisticsService.calculateAnovaTest(field, t1SurfaceLayer, t2SurfaceLayer)
        anovaStats = self.statisticsService.getAnovaStatistics(field, t1SurfaceLayer, t2SurfaceLayer)

        for statisticList in anovaStats:
            formattedStatisticList = [f'{statistic:.2f}' for statistic in statisticList]
            anovaStatsList.append(formattedStatisticList)

        return f'{pValue:.2f}', anovaStatsList

    def getRMSE(self, layer):
        firstFeature = next(layer.getFeatures()) if layer.featureCount() > 0 else None
        RMSE = firstFeature['%_rmse']
        if isinstance(RMSE, float):
            return f'RMSE = {round(RMSE, 2)}%'
        elif isinstance(RMSE, QVariant):
            RMSE.convert(38)
            return f'RMSE = {round(RMSE.value(), 2)}%'


    def getPresentationParameters(self, trialId, t1ValidationLayer, t2ValidationLayer, rootPath):

        trialResult = self.databaseFactory.fetchOne(FETCH_ONE_TRIAL, trialId, dictionary=True)
        t1Rmse = self.getRMSE(t1ValidationLayer)
        t2Rmse = self.getRMSE(t2ValidationLayer)

        histogramPath = os.path.join(rootPath, DIRECTORY_STRUCTURE['05_Results'][0])
        variogramPath = os.path.join(rootPath, DIRECTORY_STRUCTURE['05_Results'][1])
        mapsPath = os.path.join(rootPath, DIRECTORY_STRUCTURE['05_Results'][2])

        presentationData = {
            1: {1: f"Area: {trialResult[0]['field_name']}"},
            2: {
                10: self.systemService.filterByFileName(mapsPath, ['01_Points_with_measured_yield_values']),
                11: self.systemService.filterByFileName(mapsPath, ['02_T1_Measured_yield']),
                12: self.systemService.filterByFileName(mapsPath, ['03_T2_Measured_yield'])},
            3: {
                10: self.systemService.filterByFileName(histogramPath, ['Yield_Map_V']),
                11: self.systemService.filterByFileName(histogramPath, ['T1_total_V']),
                12: self.systemService.filterByFileName(histogramPath, ['T2_total_V'])},

            5: {
                10: self.systemService.filterByFileName(mapsPath, ['06_Model_T1_T2']),
                11: self.systemService.filterByFileName(mapsPath, ['07_Model_T1']),
                12: self.systemService.filterByFileName(mapsPath, ['08_Model_T2']),
                13: self.systemService.filterByFileName(variogramPath, ['0_Variograma_T1_T2_total_']),
                14: self.systemService.filterByFileName(variogramPath, ['0_Variograma_T1_total_']),
                20: self.systemService.filterByFileName(variogramPath, ['0_Variograma_T2_total_'])},
            6: {
                10: self.systemService.filterByFileName(mapsPath, ['04_T1_Sample_for_model_generation']),
                11: self.systemService.filterByFileName(mapsPath, ['07_Model_T1']),
                12: self.systemService.filterByFileName(variogramPath, ['0_Variograma_T1_80_perc_']),
                13: self.systemService.filterByFileName(histogramPath, ['T1_80_perc_H']),
                15: t1Rmse
            },
            7: {
                10: self.systemService.filterByFileName(mapsPath, ['05_T2_Sample_for_model_generation']),
                11: self.systemService.filterByFileName(mapsPath, ['08_Model_T2']),
                12: self.systemService.filterByFileName(variogramPath, ['0_Variograma_T2_80_perc_']),
                13: self.systemService.filterByFileName(histogramPath, ['T2_80_perc_H']),
                15: t2Rmse
            },
            8: {
                10: self.systemService.filterByFileName(mapsPath, ['11_Yield_gain_using_T2']),
                11: self.systemService.filterByFileName(rootPath, ['Yield_Gain_Histogram']),
                12: self.systemService.filterByFileName(rootPath, ['Gain_Statistics_Table'])}
        }

        return presentationData

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'createpresentation'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Create presentation')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Report')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'report'

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
        return QCoreApplication.translate('PresentationProcessingAlgorithm', string)

    def createInstance(self):
        return PresentationProcessingAlgorithm()
