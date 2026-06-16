# -*- co# -*- coding: utf-8 -*-
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
from qgis.core import (QgsProject, QgsProcessingParameterField,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterCrs,
                       QgsProcessingMultiStepFeedback)

from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...algorithms.algorithm_runner import AlgorithmRunner
from ...constants import QGIS_TOC_GROUPS
from ...services.layer_service import LayerService
from ...services.system_service import SystemService
from ....gui.settings.options_settings_dlg import OptionsSettingsPage
from ....gui.wrappers.filtered_layer_wrapper import ParameterFilteredLayer


class TreatmentPolygonsBuilderProcessingAlgorithm(QgsProcessingAlgorithm):
    FILTERED_LAYER = 'FILTERED_LAYER'
    GPS_POINTS_LAYER = 'GPS_POINTS_LAYER'
    BOUNDARY = 'BOUNDARY'
    SORTING_FIELD = 'SORTING_FIELD'
    METHOD = 'METHOD'
    BORDER_SIZE = 'BORDER_SIZE'
    REPROJECT = 'REPROJECT'
    OUTPUT = 'OUTPUT'
    CRS = 'CRS'
    SUGGESTED_CRS = 'SUGGESTED_CRS'

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
            ParameterFilteredLayer(
                self.GPS_POINTS_LAYER,
                description="GPS points layer",
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.REPROJECT, self.tr("Reproject if CRS is geographic")
            )
        )

        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                self.tr('Suggested CRS'),
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.SORTING_FIELD,
                self.tr('Sorting variable'),
                parentLayerParameterName=self.GPS_POINTS_LAYER,
                type=QgsProcessingParameterField.Any,
                allowMultiple=False,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.METHOD,
                self.tr('Method'),
                options=['Boucle rang', 'Ligne parcelle'],
                allowMultiple=False
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BORDER_SIZE,
                self.tr('Border size'),
                type=QgsProcessingParameterNumber.Double,
                optional=False,
                minValue=0.0
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.BOUNDARY, self.tr("Create boundary polygon")
            )
        )

    def parameterAsFilteredLayer(self, parameters, name, context):
        return parameters[name]

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        gpsLayer = self.parameterAsFilteredLayer(parameters, self.GPS_POINTS_LAYER, context)
        sortingField = self.parameterAsFields(parameters, self.SORTING_FIELD, context)
        borderSize = self.parameterAsDouble(parameters, self.BORDER_SIZE, context)
        methodId = self.parameterAsEnums(parameters, self.METHOD, context)
        boundary = self.parameterAsBool(parameters, self.BOUNDARY, context)
        reproject = self.parameterAsBool(parameters, self.REPROJECT, context)

        filePath = self.project.homePath()
        multiFeedback = QgsProcessingMultiStepFeedback(3, feedback)
        multiFeedback.pushInfo(self.tr(f'Getting treatments...'))

        treatmentPath = os.path.join(filePath, '00_Data', '00_Raw_Files', f'{gpsLayer.name()}_treatment.shp')
        boundaryLayerName = f'{gpsLayer.name()}_contour'
        boundaryLayer = os.path.join(filePath, '00_Data', '00_Raw_Files', f'{boundaryLayerName}.shp')

        treatmentPolygons = self.algRunner.runWaypointsPolygonsBuilder(gpsLayer,
                                                                       methodId[0],
                                                                       sortingField[0],
                                                                       borderSize,
                                                                       feedback=feedback,
                                                                       outputLayer=treatmentPath)

        treatment = self.layerService.loadShapeFile(QGIS_TOC_GROUPS[0], treatmentPath)
        self.layerService.createBoundaryLayerSymbology(treatment)

        if boundary:
            self.algRunner.runDissolvePolygons(treatmentPolygons, context=context, feedback=feedback,
                                               outputLayer=boundaryLayer)
            contourLayer = self.layerService.loadShapeFile(QGIS_TOC_GROUPS[0], boundaryLayer)
            self.layerService.createBoundaryLayerSymbology(contourLayer)

        if reproject:
            crsOperations = self.layerService.getSuggestedCrs(gpsLayer)
            toReproject = [treatmentPath, boundaryLayer]
            for toReprojectFilePath in toReproject:
                fileName = self.systemService.extractFileName(toReprojectFilePath)
                reprojectedName = f"{fileName}_{crsOperations[1]}.shp"
                outputLayerFilePath = os.path.join(filePath, '00_Data', '01_Reproject', reprojectedName)

                self.algRunner.runReprojectLayer(toReprojectFilePath, crsOperations[2], crsOperations[3],
                                                 context=context, feedback=feedback, outputLayer=outputLayerFilePath)
                reprojectedLayer = self.layerService.loadShapeFile(QGIS_TOC_GROUPS[1], outputLayerFilePath)
                self.layerService.createBoundaryLayerSymbology(reprojectedLayer)

        return {self.OUTPUT: None}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'treatmentpolygonsbuilder'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Treatment polygons builder')

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
        return QCoreApplication.translate('TreatmentPolygonsBuilderProcessingAlgorithm', string)

    def createInstance(self):
        return TreatmentPolygonsBuilderProcessingAlgorithm()
