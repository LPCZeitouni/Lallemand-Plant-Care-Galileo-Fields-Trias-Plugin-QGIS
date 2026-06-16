# -*- coding: utf-# -*- coding: utf-8 -*-
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
import os.path

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject, QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFile)

from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ....gui.wrappers.trial_name_wrapper import ParameterTrialName
from ...constants import FETCH_ONE_TRIAL, FETCH_ONE_FARMER, FETCH_ONE_CROP
from ...factories.postgres_factory import PostgresFactory
from ...factories.sqlite_factory import SqliteFactory
from ...services.layer_service import LayerService
from ...services.report_service import ReportService
from ...services.statistics_service import StatisticsService
from ...services.system_service import SystemService


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
        """
        Here is where the processing itself takes place.
        """

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
        self.reportService.createWordReport(reportData, tableData, imageData, outputFolder, feedback)

        return {self.OUTPUT: None}

    def getReportData(self):
        trialResult = self.databaseFactory.fetchOne(FETCH_ONE_TRIAL, self.trialId, dictionary=True)
        farmerResult = self.databaseFactory.fetchOne(FETCH_ONE_FARMER, trialResult[0]['farmer_id'], dictionary=True)
        cropResult = self.databaseFactory.fetchOne(FETCH_ONE_CROP, trialResult[0]['crop_trial_id'], dictionary=True)

        t1Mean = self.statisticsService.calculateMean(self.t1SurfaceLayer, 'yield')
        t2Mean = self.statisticsService.calculateMean(self.t2SurfaceLayer, 'yield')
        meanDifference = t1Mean - t2Mean

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
            '{MEAN_DIFFERENCE}': f'{meanDifference:.4f}'
        }

    def getTableData(self):
        fValue, pValue = self.statisticsService.calculateAnovaTest('yield', self.t1SurfaceLayer, self.t2SurfaceLayer)
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

    def getImageData(self):
        filePath = self.project.homePath()
        mapsPath = os.path.join(filePath, '05_Results', '03_Maps')
        rootPath = os.path.join(filePath, '05_Results')

        return {
            '{T1_T2_POINTS}': [self.systemService.filterByFileName(mapsPath, ['01_Points_with_measured_yield_values']), 4.32],
            '{T1_POINTS}': [self.systemService.filterByFileName(mapsPath, ['02_T1_Measured_yield']), 3.13],
            '{T2_POINTS}': [self.systemService.filterByFileName(mapsPath, ['03_T2_Measured_yield']), 3.13],
            '{T1_T2_MODEL}': [self.systemService.filterByFileName(mapsPath, ['11_Yield_gain_using_T2']), 4.32],
            '{T1_MODEL}': [self.systemService.filterByFileName(mapsPath, ['07_Model_T1']), 3.13],
            '{T2_MODEL}': [self.systemService.filterByFileName(mapsPath, ['08_Model_T2']), 3.13],
            '{YIELD_GAIN_HISTOGRAM}': [self.systemService.filterByFileName(rootPath, ['Yield_Gain_Histogram']), 5.1]
        }

    def getTotalPercentage(self):
        total, values = self.layerService.filterFeaturesByIntervals(self.gainLayer)
        percentages = self.layerService.getPercentualFromIntervals(total, values, False)
        percentages.pop(0)
        return f'{sum([float(percent) for percent in percentages]):.2f}%'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'createreport'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Create report')

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
        return QCoreApplication.translate('ReportProcessingAlgorithm', string)

    def createInstance(self):
        return ReportProcessingAlgorithm()
