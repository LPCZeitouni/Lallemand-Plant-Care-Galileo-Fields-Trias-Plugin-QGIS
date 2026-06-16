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


import os.path

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterVectorLayer
                       )

from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...constants import COMPOSER_LAYERS
from ...services.composer_service import ComposerService
from ...services.layer_service import LayerService
from ...services.message_service import MessageService
from ...services.statistics_service import StatisticsService


class LoadComposerTemplatesAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYERS = 'INPUT_LAYERS'
    TRIAL_BOUNDS_LAYER = 'TRIAL_BOUNDS_LAYER'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.project = QgsProject.instance()
        self.statistics = StatisticsService()
        self.layerService = LayerService()
        self.messageService = MessageService()
        self.layers = self.project.instance().mapLayers().values()
        self.filteredLayers = self.layerService.filterByLayerName(list(self.layers), COMPOSER_LAYERS, inverse=True)


    def initAlgorithm(self, config=None):

        # layers = self.project.instance().mapLayers().values()
        # contour = self.layerService.filterByLayerName(list(layers), ['_contour_'], inverse=True)

        # self.filteredLayers = self.layerService.filterByLayerName(list(layers), COMPOSER_LAYERS, inverse=True)
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_LAYERS,
                self.tr('Layers to add in templates'),
                options=[layer.name() for layer in self.filteredLayers],
                allowMultiple=True
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.TRIAL_BOUNDS_LAYER,
                self.tr("Trial bounds layer"),
                [QgsProcessing.TypeVectorPolygon],
                optional=False,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        layerIds = self.parameterAsEnums(parameters, self.INPUT_LAYERS, context)
        trialBoundsLayer = self.parameterAsVectorLayer(parameters, self.TRIAL_BOUNDS_LAYER, context)

        totalFeatures = len(self.filteredLayers)
        progressPerFeature = 100.0 / totalFeatures if totalFeatures else 0

        composerService = ComposerService(self.project)
        layerLayoutMapping = composerService.mapLayersToLayouts([self.filteredLayers[layerId] for layerId in layerIds])

        multiFeedback = QgsProcessingMultiStepFeedback(totalFeatures, feedback)
        # gainLayer = QgsProject.instance().mapLayersByName('Gain_Points')[0]
        # self.statistics.runStatistics(gainLayer)

        if not trialBoundsLayer:
            multiFeedback.reportError(self.tr('\nERROR: No valid extent layer...\n'))
        else:
            for layer, layoutPath in layerLayoutMapping.items():

                if multiFeedback.isCanceled():
                    self.messageService.criticalMessageBar('Loading templates', 'operation aborted by the user!')
                    break

                if os.path.isfile(layoutPath):
                    layout = composerService.createLayout(trialBoundsLayer)
                    composerService.loadLayoutFromTemplate(layout, layoutPath)
                    composerService.updateComposerLayout(layout, layer, trialBoundsLayer)

                    result = self.project.layoutManager().addLayout(layout)
                    multiFeedback.pushInfo(self.tr(f'Loading layout {layout.name()}.'))
                    if result:
                        multiFeedback.pushInfo(self.tr('Layout template loaded successfully!\n'))
                        self.messageService.logMessage(f'Loading layout {layout.name()}: SUCCESS', 3)
                        progressIndex = list(layerLayoutMapping.keys()).index(layer)
                        feedback.setProgress(int(progressIndex * progressPerFeature))
                    else:
                        multiFeedback.reportError(self.tr(f'Layout {layout.name()} could not be loaded!\n'))
                        self.messageService.logMessage(f'Loading layout {layout.name()}: FAILED', 2)

        return {self.OUTPUT: None}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'loadcomposertemplates'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Load composer templates')

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
        return QCoreApplication.translate('LoadComposerTemplatesAlgorithm', string)

    def createInstance(self):
        return LoadComposerTemplatesAlgorithm()
