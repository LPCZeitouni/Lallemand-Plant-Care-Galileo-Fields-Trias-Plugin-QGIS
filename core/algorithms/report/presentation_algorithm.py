# -*- coding: utf-8 -*-
"""
LallemandGeostatFieldTrialTreatments

A QGIS plugin for agronomic field trial analysis using geostatistical
(Kriging-based) models to analyze and compare treatment scenarios.
"""

import os.path

from qgis.PyQt.Qt import QVariant
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProject,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFile
)

from ....gui.wrappers.trial_name_wrapper import ParameterTrialName
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...constants import FETCH_ONE_TRIAL, DIRECTORY_STRUCTURE
from ...factories.sqlite_factory import SqliteFactory
from ...services.plot_service import PlotterService
from ...services.report_service import ReportService
from ...services.statistics_service import StatisticsService
from ...services.system_service import SystemService
from ...services.final_surface_symbology_service import FinalSurfaceSymbologyService


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
        self.finalSurfaceSymbologyService = FinalSurfaceSymbologyService()

    def initAlgorithm(self, config=None):

        self.addParameter(
            ParameterTrialName(
                self.TRIAL_NAME,
                description="Trial name"
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T1_SURFACE,
                self.tr('T1 final surface points layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T2_SURFACE,
                self.tr('T2 final surface points layer'),
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

        pValue, anovaStats = self.getAnovaStatistics(
            t1SurfaceLayer,
            t2SurfaceLayer,
            yieldField[0]
        )

        gainStats = self.getGainStatistics(gainLayer, yieldField[0])

        self.plotService.createGainStatisticsTable(
            pValue,
            gainStats,
            anovaStats,
            True,
            rootPath
        )

        presentationData = self.getPresentationParameters(
            trialId,
            t1ValidationLayer,
            t2ValidationLayer,
            rootPath
        )

        self.reportService.createPresentation(
            presentationData,
            outputFolder
        )

        return {self.OUTPUT: None}

    def getGainStatistics(self, gainLayer, field):
        gainStatsList = []
        gainStats = self.statisticsService.getGainStatistics(gainLayer, field)

        for statistic in gainStats:
            gainStatsList.append([f'{statistic:.2f}'])

        return gainStatsList

    def getAnovaStatistics(self, t1SurfaceLayer, t2SurfaceLayer, field):
        anovaStatsList = []

        fValue, pValue = self.statisticsService.calculateAnovaTest(
            field,
            t1SurfaceLayer,
            t2SurfaceLayer
        )

        anovaStats = self.statisticsService.getAnovaStatistics(
            field,
            t1SurfaceLayer,
            t2SurfaceLayer
        )

        for statisticList in anovaStats:
            formattedStatisticList = [
                f'{statistic:.2f}'
                for statistic in statisticList
            ]
            anovaStatsList.append(formattedStatisticList)

        return f'{pValue:.2f}', anovaStatsList

    def getRMSE(self, layer):
        firstFeature = next(layer.getFeatures()) if layer.featureCount() > 0 else None

        if firstFeature is None:
            return 'RMSE = N/A'

        RMSE = firstFeature['%_rmse']

        if isinstance(RMSE, float):
            return f'RMSE = {round(RMSE, 2)}%'

        elif isinstance(RMSE, QVariant):
            RMSE.convert(38)
            return f'RMSE = {round(RMSE.value(), 2)}%'

        try:
            return f'RMSE = {round(float(RMSE), 2)}%'
        except Exception:
            return 'RMSE = N/A'

    def findFirstExistingMap(self, folderPath, patternGroups):
        for patterns in patternGroups:
            result = self.systemService.filterByFileName(folderPath, patterns)
            if result:
                return result

        return None

    def getPresentationParameters(self, trialId, t1ValidationLayer, t2ValidationLayer, rootPath):

        trialResult = self.databaseFactory.fetchOne(
            FETCH_ONE_TRIAL,
            trialId,
            dictionary=True
        )

        t1Rmse = self.getRMSE(t1ValidationLayer)
        t2Rmse = self.getRMSE(t2ValidationLayer)

        histogramPath = os.path.join(rootPath, DIRECTORY_STRUCTURE['05_Results'][0])
        variogramPath = os.path.join(rootPath, DIRECTORY_STRUCTURE['05_Results'][1])
        mapsPath = os.path.join(rootPath, DIRECTORY_STRUCTURE['05_Results'][2])

        t1FinalSurfaceMap = self.findFirstExistingMap(
            mapsPath,
            [
                ['T1_Final_Surface'],
                ['09_T1_Final_Surface'],
                ['T1_Final'],
                ['07_Model_T1']
            ]
        )

        t2FinalSurfaceMap = self.findFirstExistingMap(
            mapsPath,
            [
                ['T2_Final_Surface'],
                ['10_T2_Final_Surface'],
                ['T2_Final'],
                ['08_Model_T2']
            ]
        )

        controlScaleNote = self.finalSurfaceSymbologyService.getControlScaleNote()

        presentationData = {
            '_CONTROL_SCALE_NOTE': controlScaleNote,

            1: {
                1: f"Area: {trialResult[0]['field_name']}"
            },

            2: {
                10: self.systemService.filterByFileName(
                    mapsPath,
                    ['01_Points_with_measured_yield_values']
                ),
                11: self.systemService.filterByFileName(
                    mapsPath,
                    ['02_T1_Measured_yield']
                ),
                12: self.systemService.filterByFileName(
                    mapsPath,
                    ['03_T2_Measured_yield']
                )
            },

            3: {
                10: self.systemService.filterByFileName(
                    histogramPath,
                    ['Yield_Map_V']
                ),
                11: self.systemService.filterByFileName(
                    histogramPath,
                    ['T1_total_V']
                ),
                12: self.systemService.filterByFileName(
                    histogramPath,
                    ['T2_total_V']
                )
            },

            5: {
                10: self.systemService.filterByFileName(
                    mapsPath,
                    ['06_Model_T1_T2']
                ),
                11: t1FinalSurfaceMap,
                12: t2FinalSurfaceMap,
                13: self.systemService.filterByFileName(
                    variogramPath,
                    ['0_Variograma_T1_T2_total_']
                ),
                14: self.systemService.filterByFileName(
                    variogramPath,
                    ['0_Variograma_T1_total_']
                ),
                20: self.systemService.filterByFileName(
                    variogramPath,
                    ['0_Variograma_T2_total_']
                )
            },

            6: {
                10: self.systemService.filterByFileName(
                    mapsPath,
                    ['04_T1_Sample_for_model_generation']
                ),
                11: t1FinalSurfaceMap,
                12: self.systemService.filterByFileName(
                    variogramPath,
                    ['0_Variograma_T1_80_perc_']
                ),
                13: self.systemService.filterByFileName(
                    histogramPath,
                    ['T1_80_perc_H']
                ),
                15: t1Rmse
            },

            7: {
                10: self.systemService.filterByFileName(
                    mapsPath,
                    ['05_T2_Sample_for_model_generation']
                ),
                11: t2FinalSurfaceMap,
                12: self.systemService.filterByFileName(
                    variogramPath,
                    ['0_Variograma_T2_80_perc_']
                ),
                13: self.systemService.filterByFileName(
                    histogramPath,
                    ['T2_80_perc_H']
                ),
                15: t2Rmse
            },

            8: {
                10: self.systemService.filterByFileName(
                    mapsPath,
                    ['11_Yield_gain_using_T2']
                ),
                11: self.systemService.filterByFileName(
                    rootPath,
                    ['Yield_Gain_Histogram']
                ),
                12: self.systemService.filterByFileName(
                    rootPath,
                    ['Gain_Statistics_Table']
                )
            }
        }

        return presentationData

    def name(self):
        return 'createpresentation'

    def displayName(self):
        return self.tr('Create presentation')

    def group(self):
        return self.tr('Report')

    def groupId(self):
        return 'report'

    def shortHelpString(self):
        return ProcessingAlgorithmHelpCreator.shortHelpString(self.name())

    def tr(self, string):
        return QCoreApplication.translate(
            'PresentationProcessingAlgorithm',
            string
        )

    def createInstance(self):
        return PresentationProcessingAlgorithm()
