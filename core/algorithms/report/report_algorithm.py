# -*- coding: utf-8 -*-
"""
LallemandGeostatFieldTrialTreatments

A QGIS plugin for agronomic field trial analysis using geostatistical
(Kriging-based) models to analyze and compare treatment scenarios.
"""

import os.path

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProject,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFile
)

from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ....gui.wrappers.trial_name_wrapper import ParameterTrialName
from ...constants import FETCH_ONE_TRIAL, FETCH_ONE_FARMER, FETCH_ONE_CROP
from ...factories.sqlite_factory import SqliteFactory
from ...services.layer_service import LayerService
from ...services.report_service import ReportService
from ...services.statistics_service import StatisticsService
from ...services.system_service import SystemService
from ...services.final_surface_symbology_service import FinalSurfaceSymbologyService


class ReportProcessingAlgorithm(QgsProcessingAlgorithm):

    TRIAL_NAME = 'TRIAL_NAME'
    YIELD = 'YIELD'
    T1_LAYER = 'T1_LAYER'
    T2_LAYER = 'T2_LAYER'
    T1_SURFACE = 'T1_SURFACE'
    T2_SURFACE = 'T2_SURFACE'
    GAIN_POINTS = 'GAIN_POINTS'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.layerService = LayerService()
        self.databaseFactory = SqliteFactory()
        self.project = QgsProject.instance()
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
                self.YIELD,
                self.tr('Yield layer (T1 and T2)'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T1_LAYER,
                self.tr('T1 total points layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T2_LAYER,
                self.tr('T2 total points layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T1_SURFACE,
                self.tr('T1 Surface points layer'),
                [QgsProcessing.TypeVectorPoint],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.T2_SURFACE,
                self.tr('T2 Surface points layer'),
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

    def parameterAsTrial(self, parameters, name, context):
        return parameters[name]

    def processAlgorithm(self, parameters, context, feedback):

        self.trialId = self.parameterAsTrial(parameters, self.TRIAL_NAME, context)
        self.yieldLayer = self.parameterAsVectorLayer(parameters, self.YIELD, context)
        self.t1Layer = self.parameterAsVectorLayer(parameters, self.T1_LAYER, context)
        self.t2Layer = self.parameterAsVectorLayer(parameters, self.T2_LAYER, context)
        self.t1SurfaceLayer = self.parameterAsVectorLayer(parameters, self.T1_SURFACE, context)
        self.t2SurfaceLayer = self.parameterAsVectorLayer(parameters, self.T2_SURFACE, context)
        self.gainLayer = self.parameterAsVectorLayer(parameters, self.GAIN_POINTS, context)

        outputFolder = self.parameterAsFile(parameters, self.OUTPUT, context)

        reportData = self.getReportData()
        tableData = self.getTableData()
        imageData = self.getImageData()

        self.reportService.createWordReport(
            reportData,
            tableData,
            imageData,
            outputFolder,
            feedback
        )

        return {self.OUTPUT: None}

    def getReportData(self):
        trialResult = self.databaseFactory.fetchOne(
            FETCH_ONE_TRIAL,
            self.trialId,
            dictionary=True
        )

        farmerResult = self.databaseFactory.fetchOne(
            FETCH_ONE_FARMER,
            trialResult[0]['farmer_id'],
            dictionary=True
        )

        cropResult = self.databaseFactory.fetchOne(
            FETCH_ONE_CROP,
            trialResult[0]['crop_trial_id'],
            dictionary=True
        )

        t1Mean = self.statisticsService.calculateMean(self.t1SurfaceLayer, 'yield')
        t2Mean = self.statisticsService.calculateMean(self.t2SurfaceLayer, 'yield')
        meanDifference = t1Mean - t2Mean

        controlScaleNote = self.finalSurfaceSymbologyService.getControlScaleNote()

        return {
            '{FIELD_NAME}': trialResult[0]['field_name'],
            '{field_area}': trialResult[0]['field_area'],
            '{crop_name}': cropResult[0]['crop_name'],
            '{variety}': cropResult[0]['variety'],
            '{sowing_date}': cropResult[0]['sowing_date'],
            '{harvest_date}': cropResult[0]['harvest_date'],
            '{inter_ro_cm}': str(cropResult[0]['inter_ro_cm']),
            '{field_soil}': trialResult[0]['field_soil'],
            '{field_irrigation}': str(trialResult[0]['field_irrigation']),
            '{first_name}': farmerResult[0]['first_name'],
            '{last_name}': farmerResult[0]['last_name'],
            '{town}': farmerResult[0]['town'],
            '{zipcode}': farmerResult[0]['zipcode'],
            '{TOTAL_YIELD_POINTS}': f'{self.yieldLayer.featureCount()}',
            '{TOTAL_T1_POINTS}': f'{self.t1Layer.featureCount()}',
            '{TOTAL_T2_POINTS}': f'{self.t2Layer.featureCount()}',
            '{TOTAL_PERCENTAGE}': self.getTotalPercentage(),
            '{MEAN_DIFFERENCE}': f'{meanDifference:.4f}',
            '{CONTROL_SCALE_NOTE}': controlScaleNote
        }

    def getTableData(self):
        fValue, pValue = self.statisticsService.calculateAnovaTest(
            'yield',
            self.t1SurfaceLayer,
            self.t2SurfaceLayer
        )

        t1Mean = self.statisticsService.calculateMean(self.t1SurfaceLayer, 'yield')
        t2Mean = self.statisticsService.calculateMean(self.t2SurfaceLayer, 'yield')

        t1StdDev = self.statisticsService.calculateStdDev(self.t1SurfaceLayer, 'yield')
        t2StdDev = self.statisticsService.calculateStdDev(self.t2SurfaceLayer, 'yield')

        return {
            '{P_VALUE}': f'{pValue:.4f}',
            '{T1_MEAN}': f'{t1Mean:.4f}',
            '{T2_MEAN}': f'{t2Mean:.4f}',
            '{T1_STD_DEV}': f'{t1StdDev:.4f}',
            '{T2_STD_DEV}': f'{t2StdDev:.4f}'
        }

    def findFirstExistingMap(self, folderPath, patternGroups):
        """
        Return the first file matching one of the provided pattern groups.
        """

        for patterns in patternGroups:
            result = self.systemService.filterByFileName(folderPath, patterns)
            if result:
                return result

        return None

    def getImageData(self):
        filePath = self.project.homePath()
        mapsPath = os.path.join(filePath, '05_Results', '03_Maps')
        rootPath = os.path.join(filePath, '05_Results')

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

        return {
            '{T1_T2_POINTS}': [
                self.systemService.filterByFileName(
                    mapsPath,
                    ['01_Points_with_measured_yield_values']
                ),
                4.32
            ],
            '{T1_POINTS}': [
                self.systemService.filterByFileName(
                    mapsPath,
                    ['02_T1_Measured_yield']
                ),
                3.13
            ],
            '{T2_POINTS}': [
                self.systemService.filterByFileName(
                    mapsPath,
                    ['03_T2_Measured_yield']
                ),
                3.13
            ],
            '{T1_T2_MODEL}': [
                self.systemService.filterByFileName(
                    mapsPath,
                    ['11_Yield_gain_using_T2']
                ),
                4.32
            ],
            '{T1_MODEL}': [
                t1FinalSurfaceMap,
                3.13
            ],
            '{T2_MODEL}': [
                t2FinalSurfaceMap,
                3.13
            ],
            '{YIELD_GAIN_HISTOGRAM}': [
                self.systemService.filterByFileName(
                    rootPath,
                    ['Yield_Gain_Histogram']
                ),
                5.1
            ]
        }

    def getTotalPercentage(self):
        total, values = self.layerService.filterFeaturesByIntervals(self.gainLayer)
        percentages = self.layerService.getPercentualFromIntervals(total, values, False)
        percentages.pop(0)

        return f'{sum([float(percent) for percent in percentages]):.2f}%'

    def name(self):
        return 'createreport'

    def displayName(self):
        return self.tr('Create report')

    def group(self):
        return self.tr('Report')

    def groupId(self):
        return 'report'

    def shortHelpString(self):
        return ProcessingAlgorithmHelpCreator.shortHelpString(self.name())

    def tr(self, string):
        return QCoreApplication.translate(
            'ReportProcessingAlgorithm',
            string
        )

    def createInstance(self):
        return ReportProcessingAlgorithm()
