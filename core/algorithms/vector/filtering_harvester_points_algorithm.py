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
QgsProcessingParameterCrs,
                       QgsProcessingMultiStepFeedback)

from ....gui.wrappers.filtering_wrapper import ParameterFiltering
from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...algorithms.algorithm_runner import AlgorithmRunner
from ...constants import QGIS_TOC_GROUPS
from ...services.layer_service import LayerService
from ...services.system_service import SystemService
from ....gui.settings.options_settings_dlg import OptionsSettingsPage
from ....gui.wrappers.filtered_layer_wrapper import ParameterFilteredLayer


class FilteringHarvesterPointsProcessingAlgorithm(QgsProcessingAlgorithm):
    HARVESTER_POINTS_LAYER = 'HARVESTER_POINTS_LAYER'
    REPROJECT = 'REPROJECT'
    ID_FIELD = 'ID_FIELD'
    YIELD_FIELD = 'YIELD_FIELD'
    TREATMENT_POLYGONS = 'TREATMENT_POLYGONS'
    TREATMENT_ID_FIELD = 'TREATMENT_ID_FIELD'
    BOUNDARY_POLYGON = 'BOUNDARY_POLYGON'
    TARGET_PROJECTION = 'TARGET_PROJECTION'
    DATE_COLUMN = 'DATE_COLUMN'
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
            ParameterFiltering(
                self.HARVESTER_POINTS_LAYER,
                description=self.tr('Harvester points layer'),
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.REPROJECT, self.tr("Reproject if CRS is geographic")
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD,
                self.tr('ID field'),
                parentLayerParameterName=self.HARVESTER_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.YIELD_FIELD,
                self.tr('Yield field'),
                parentLayerParameterName=self.HARVESTER_POINTS_LAYER,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.TREATMENT_POLYGONS,
                self.tr('Treatment polygons layer'),
                [QgsProcessing.TypeVectorPolygon],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.TREATMENT_ID_FIELD,
                self.tr('Treatment identifier field'),
                parentLayerParameterName=self.TREATMENT_POLYGONS,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.BOUNDARY_POLYGON,
                self.tr('Contour polygon layer'),
                [QgsProcessing.TypeVectorPolygon],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.TARGET_PROJECTION,
                self.tr('Target projection'),
                options=['Lambert93', 'UTM'],
                allowMultiple=False,
                defaultValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.DATE_COLUMN,
                self.tr('Date column'),
                options=['Yes', 'No'],
                allowMultiple=False,
                defaultValue=0
            )
        )

    def parameterAsFilteredLayer(self, parameters, name, context):
        return parameters[name]

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # harvesterLayer = self.parameterAsVectorLayer(parameters, self.HARVESTER_POINTS_LAYER, context)
        harvesterLayer = self.parameterAsFilteredLayer(parameters, self.HARVESTER_POINTS_LAYER, context)
        reproject = self.parameterAsBool(parameters, self.REPROJECT, context)
        idField = self.parameterAsFields(parameters, self.ID_FIELD, context)
        yieldField = self.parameterAsFields(parameters, self.YIELD_FIELD, context)
        treatmentLayer = self.parameterAsVectorLayer(parameters, self.TREATMENT_POLYGONS, context)
        treatmentIdField = self.parameterAsFields(parameters, self.TREATMENT_ID_FIELD, context)
        boundaryLayer = self.parameterAsVectorLayer(parameters, self.BOUNDARY_POLYGON, context)
        targetProjection = self.parameterAsEnums(parameters, self.TARGET_PROJECTION, context)
        dateColumn = self.parameterAsEnums(parameters, self.DATE_COLUMN, context)

        multiFeedback = QgsProcessingMultiStepFeedback(3, feedback)
        multiFeedback.pushInfo(self.tr(f'Initializing filter...\n'))

        filePath = self.project.homePath()
        yieldMapPath = os.path.join(filePath, '00_Data', '00_Raw_Files', 'Yield_Map.shp')
        filterParameters = self.getYieldFilteringParameters(boundaryLayer, treatmentLayer, treatmentIdField[0],
                                                            harvesterLayer, idField[0], yieldField[0],
                                                            targetProjection[0], dateColumn[0], filePath)


        output = AlgorithmRunner().runYieldMapFiltering(filterParameters, context=context, feedback=feedback)

        multiFeedback.pushInfo(self.tr(f'Selecting features...\n'))
        filteredFeatures = self.layerService.getFeaturesByRequest(output, "\"Biais_rendement\"='F - Pas de biais'")

        yieldMapVector = self.layerService.createMemoryVectorLayer(harvesterLayer.wkbType(), 'Yield_Map',
                                                                   harvesterLayer.crs().authid(),
                                                                   fields=output.fields(),
                                                                   features=filteredFeatures)

        self.layerService.saveVectorLayer(yieldMapVector, yieldMapPath)
        multiFeedback.pushInfo(self.tr(f'Loading layer...\n'))
        self.layerService.loadShapeFile(QGIS_TOC_GROUPS[0], yieldMapPath)

        if reproject:
            crsOperations = self.layerService.getSuggestedCrs(harvesterLayer)
            outputReprojectLayer = os.path.join(filePath, '00_Data', '01_Reproject', 'T1_T2_total.shp')
            multiFeedback.pushInfo(self.tr(f'Reprojecting layer...\n'))
            AlgorithmRunner.runReprojectLayer(yieldMapVector, crsOperations[2], crsOperations[3],
                                              context=context, feedback=feedback,
                                              outputLayer=outputReprojectLayer)

            reprojectedLoadedLayer = self.layerService.loadShapeFile(QGIS_TOC_GROUPS[2], outputReprojectLayer)
            multiFeedback.pushInfo(self.tr(f'Applying symbology...\n'))
            self.layerService.applySymbology(reprojectedLoadedLayer, yieldField[0])

            yieldHistogramPath = os.path.join(filePath, '05_Results', '01_Histograms')

            multiFeedback.pushInfo(self.tr(f'Exporting histogram...\n'))
            yieldStatisticsTable = self.getHistogramParameters(yieldMapVector, yieldField[0])
            self.layerService.populateFrequencyHistogram(yieldMapVector, yieldField[0],
                                                         yieldStatisticsTable,
                                                         yieldHistogramPath)

        return {self.OUTPUT: None}

    def getHistogramParameters(self, layer, field):
        statisticFields = ['COUNT', 'MIN', 'MAX', 'SUM', 'MEAN', 'STD_DEV', 'CV']
        statisticValues = self.getLayerStatistics(layer, field)
        tableData = list()

        for statistic in statisticFields:
            if statistic == 'COUNT':
                tableData.append([f'{float(statisticValues[statistic]):.0f}'])
            else:
                tableData.append([f'{float(statisticValues[statistic]):.2f}'])

        return tableData

    @staticmethod
    def getLayerStatistics(layer, field):
        return AlgorithmRunner().runBasicStatisticsForFields(layer, field)

    def getYieldFilteringParameters(self, boundaryLayer, treatmentPolygons, treatmentIdentifierField, harvesterLayer,
                                    harvesterIdField, yieldField, targetProjection, dateColumn, outputFolder):
        settings = OptionsSettingsPage().getTreatmentPolygonsSettings()

        return {
            'Contour': boundaryLayer,
            'Polygones_traitement': treatmentPolygons,
            'Identifiant_polygones': treatmentIdentifierField,
            'Carte_rendement': harvesterLayer,
            'Datage': harvesterIdField,
            'Rendement': yieldField,
            'Target_Projection': targetProjection,
            'Polygones_pairs': settings[0][1],
            'Polygones_impairs': settings[0][0],
            'Colonne_date': dateColumn,
            'Largeur_coupe': settings[1],
            'Sous_Echantillonnage': settings[2],
            'RPLOTS': os.path.join(outputFolder, '00_Data', '00_Raw_Files', 'rPlots.html'),
            'Carte_filtree': 'TEMPORARY_OUTPUT',
            'Table_errors': os.path.join(outputFolder, '00_Data', '00_Raw_Files', 'table_errors.csv')
        }

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'filteringharvesterpoints'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Filtering harvester points')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Vector Creation')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'vectorcreation'

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
        return QCoreApplication.translate('FilteringHarvesterPointsProcessingAlgorithm', string)

    def createInstance(self):
        return FilteringHarvesterPointsProcessingAlgorithm()
