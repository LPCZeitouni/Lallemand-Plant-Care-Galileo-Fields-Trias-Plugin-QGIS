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
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingOutputNumber,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       )

from ..help.algorithms_help import ProcessingAlgorithmHelpCreator
from ...services.composer_service import ComposerService
from ...services.message_service import MessageService


class ExportMapsProcessingAlgorithm(QgsProcessingAlgorithm):

    LAYOUTS = 'LAYOUTS'
    EXTENSION = 'EXTENSION'
    RESOLUTION = 'RESOLUTION'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.messageService = MessageService()

    def initAlgorithm(self, config=None):

        self.layoutList = sorted(
            [composerLayout.name() for composerLayout in QgsProject.instance().layoutManager().printLayouts()],
            key=str.lower)
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

        multiFeedback = QgsProcessingMultiStepFeedback(len(layouts), feedback)
        total = 100.0 / len(layouts) if len(layouts) else 0

        if not os.path.isdir(outputFolder):
            multiFeedback.reportError(self.tr('\nERROR: No valid output folder given. We cannot continue...\n'))
        else:
            for layoutId in layoutIds:

                if multiFeedback.isCanceled():
                    self.messageService.criticalMessageBar('Exporting maps', 'operation aborted by the user!')
                    break
                layout = project.layoutManager().layoutByName(self.layoutList[layoutId])
                result = composerService.createLayoutExporter(layout, layout.name(), path=outputFolder)
                multiFeedback.pushInfo(self.tr(f'Exporting map from layout {layout.name()}.'))

                if result:
                    multiFeedback.pushInfo(self.tr('Map exported successfully!\n'))
                    self.messageService.logMessage(f'Exporting map from layout {layout.name()}: SUCCESS', 3)
                    feedback.setProgress(int(layoutId * total))
                else:
                    multiFeedback.reportError(self.tr('Map could not be exported!\n'))
                    self.messageService.logMessage(f'Exporting map from layout {layout.name()}: FAILED', 2)

        return {self.OUTPUT: None}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'exportmaps'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Export maps')

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
        return QCoreApplication.translate('ExportMapsProcessingAlgorithm', string)

    def createInstance(self):
        return ExportMapsProcessingAlgorithm()
