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

from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtWidgets import QWidget
from qgis.core import QgsMapLayer

from .filter.filtering_harvester_points import FilteringHarvesterPoints
from .geostatistics_trial.geostatistics_trial_dlg import GeostatisticsTrial
from .kriging.kriging_dlg import OrdinaryKriging
from .layer_manager.load_files_dlg import LoadFiles
from .lpc_team.farmer_manager_dlg import FarmerManager
from .lpc_team.team_manager_dlg import RegisterLpcTeam
from .report.analysis_report import AnalysisReport
from .toolbar.toolbar_form_base import Ui_Form
from .treatment.treatment_polygons import TreatmentPolygons
from .validation.sampling_layers_validation import SamplingLayersValidation
from ..core.algorithms.algorithm_runner import AlgorithmRunner
from ..core.constants import QGIS_TOC_GROUPS
from ..core.services.layer_service import LayerService


class ToolbarManager(QWidget, Ui_Form):
    def __init__(self, iface, toolbar=None):
        """Constructor."""
        super(ToolbarManager, self).__init__()
        self.setupUi(self)
        self.iface = iface
        self.toolbar = toolbar
        self.actions = list()
        self.layerService = LayerService()
        self.algRunner = AlgorithmRunner()
        self.splitter.hide()
        self.createTrialPushButton.clicked.connect(self.createTrialProject)
        self.loadFilePushButton.clicked.connect(self.loadFiles)
        self.lpcTeamPushButton.clicked.connect(self.manageLpcTeam)
        self.farmerPushButton.clicked.connect(self.manageFarmer)
        self.treatmentPushButton.clicked.connect(self.treatments)
        self.filterPushButton.clicked.connect(self.filtering)
        self.krigingPushButton.clicked.connect(self.ordinaryKriging)
        self.samplingValidationPushButton.clicked.connect(self.validation)
        self.clearStructurePushButton.clicked.connect(self.clearTreeView)
        self.reportPushButton.clicked.connect(self.getReport)
        self.mapsPushButton.clicked.connect(self.composer)
        self.exportMapPushButton.clicked.connect(self.exportMaps)
        self.samplingPushButton.clicked.connect(self.sampling)
        self.gainSurfacePushButton.clicked.connect(self.gainSurface)
        self.presentationPushButton.clicked.connect(self.getPresentation)
        self.errorCompensationPushButton.clicked.connect(self.errorCompensation)

    def unload(self):
        pass

    @pyqtSlot(bool, name="on_showToolbarPushButton_toggled")
    def toggleToolbar(self, toggled=None):
        """
        Shows/Hides the toolbar showAccountPushButton
        """
        if toggled is None:
            toggled = self.showToolbarPushButton.isChecked()
        if toggled:
            self.splitter.show()
        else:
            self.splitter.hide()

    @staticmethod
    def createTrialProject():
        """
        Shows the dialog that loads layers from server
        """
        dlg = GeostatisticsTrial()
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def loadFiles(self):
        project = self.layerService.checkForSavedProject()
        if project:
            dlg = LoadFiles(project)
            dlg.show()
            result = dlg.exec_()
            if result:
                pass

    @staticmethod
    def manageLpcTeam():
        dlg = RegisterLpcTeam()
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    @staticmethod
    def manageFarmer():
        dlg = FarmerManager()
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def treatments(self):
        project = self.layerService.checkForSavedProject()
        if project:
            TreatmentPolygons(project).runTreatmentPolygons()

    def filtering(self):
        project = self.layerService.checkForSavedProject()
        if project:
            FilteringHarvesterPoints(project).runHarvesterFilter()

    def ordinaryKriging(self):
        project = self.layerService.checkForSavedProject()
        if project:
            dlg = OrdinaryKriging(self.iface, project)
            dlg.show()
            result = dlg.exec_()
            if result:
                pass

    def validation(self):
        project = self.layerService.checkForSavedProject()
        if project:
            SamplingLayersValidation(project).runCalculateError()

    def errorCompensation(self):
        project = self.layerService.checkForSavedProject()
        if project:
            SamplingLayersValidation(project).runErrorCompensation()

    def gainSurface(self):
        project = self.layerService.checkForSavedProject()
        if project:
            SamplingLayersValidation(project).runGainSurface()

    def clearTreeView(self):
        project = self.layerService.checkForSavedProject()
        root = project.layerTreeRoot()
        if project:
            for index, layer in enumerate(self.iface.mapCanvas().layers()):
                if layer.type() == QgsMapLayer.RasterLayer:
                    layer_node = root.findLayer(layer.id())

                    if 'validation' in layer.name().split('_'):
                        self.layerService.applySymbology(layer, '', raster=True)
                        self.layerService.addMapLayer(layer, QGIS_TOC_GROUPS[5])
                    else:
                        self.layerService.applySymbology(layer, '', raster=True)
                        self.layerService.addMapLayer(layer, QGIS_TOC_GROUPS[3])

                    parent = layer_node.parent()
                    parent.removeChildNode(layer_node)

    def getReport(self):
        project = self.layerService.checkForSavedProject()
        if project:
            AnalysisReport(project).runCreateReport()

    def getPresentation(self):
        project = self.layerService.checkForSavedProject()
        if project:
            AnalysisReport(project).runCreatePresentation()

    def composer(self):
        project = self.layerService.checkForSavedProject()
        if project:
            self.algRunner.runLoadComposerTemplates(project)

    def exportMaps(self):
        project = self.layerService.checkForSavedProject()
        if project:
            self.algRunner.runExportMaps(project)

    def sampling(self):
        project = self.layerService.checkForSavedProject()
        if project:
            SamplingLayersValidation(project).runCreateSampleLayersParameters()
