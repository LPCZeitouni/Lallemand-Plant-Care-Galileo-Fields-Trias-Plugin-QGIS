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
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber
)

from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...services.composer_service import ComposerService
from ...services.message_service import MessageService
from ...services.final_surface_symbology_service import FinalSurfaceSymbologyService


class ExportMapsProcessingAlgorithm(QgsProcessingAlgorithm):

    LAYOUTS = 'LAYOUTS'
    EXTENSION = 'EXTENSION'
    RESOLUTION = 'RESOLUTION'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.messageService = MessageService()
        self.finalSurfaceSymbologyService = FinalSurfaceSymbologyService()

    def initAlgorithm(self, config=None):

        self.layoutList = sorted(
            [
                composerLayout.name()
                for composerLayout in QgsProject.instance().layoutManager().printLayouts()
            ],
            key=str.lower
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.LAYOUTS,
                self.tr('Layouts to export'),
                options=self.layoutList,
                allowMultiple=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.RESOLUTION,
                self.tr('Export resolution (if not set, the layout resolution is used)'),
                optional=True,
                minValue=1
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

        outputFolder = self.parameterAsFile(parameters, self.OUTPUT, context)
        layoutIds = self.parameterAsEnums(parameters, self.LAYOUTS, context)

        project = QgsProject.instance()
        layouts = project.layoutManager().printLayouts()

        composerService = ComposerService(project)

        # Apply common symbology before exporting layouts.
        self.finalSurfaceSymbologyService.applyControlSymbologyToFinalSurfaces()

        multiFeedback = QgsProcessingMultiStepFeedback(len(layouts), feedback)
        total = 100.0 / len(layouts) if len(layouts) else 0

        if not os.path.isdir(outputFolder):
            multiFeedback.reportError(
                self.tr('\nERROR: No valid output folder given. We cannot continue...\n')
            )

        else:
            for layoutId in layoutIds:

                if multiFeedback.isCanceled():
                    self.messageService.criticalMessageBar(
                        'Exporting maps',
                        'operation aborted by the user!'
                    )
                    break

                layout = project.layoutManager().layoutByName(
                    self.layoutList[layoutId]
                )

                result = composerService.createLayoutExporter(
                    layout,
                    layout.name(),
                    path=outputFolder
                )

                multiFeedback.pushInfo(
                    self.tr(f'Exporting map from layout {layout.name()}.')
                )

                if result:
                    multiFeedback.pushInfo(self.tr('Map exported successfully!\n'))
                    self.messageService.logMessage(
                        f'Exporting map from layout {layout.name()}: SUCCESS',
                        3
                    )
                    feedback.setProgress(int(layoutId * total))

                else:
                    multiFeedback.reportError(self.tr('Map could not be exported!\n'))
                    self.messageService.logMessage(
                        f'Exporting map from layout {layout.name()}: FAILED',
                        2
                    )

        return {self.OUTPUT: None}

    def name(self):
        return 'exportmaps'

    def displayName(self):
        return self.tr('Export maps')

    def group(self):
        return self.tr('Report')

    def groupId(self):
        return 'report'

    def shortHelpString(self):
        return ProcessingAlgorithmHelpCreator.shortHelpString(self.name())

    def tr(self, string):
        return QCoreApplication.translate(
            'ExportMapsProcessingAlgorithm',
            string
        )

    def createInstance(self):
        return ExportMapsProcessingAlgorithm()
