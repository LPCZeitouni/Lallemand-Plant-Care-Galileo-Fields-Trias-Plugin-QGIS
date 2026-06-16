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
from qgis.PyQt import QtWidgets
from qgis.core import QgsProject, QgsCoordinateReferenceSystem

from .load_files_dlg_base import Ui_LoadFilesDialogBase
from ...core.constants import QGIS_TOC_GROUPS
from ...core.services.layer_service import LayerService
from ...core.services.message_service import UserFeedback
from ...core.services.system_service import SystemService
from ...core.services.widget_service import WidgetService
from ...core.algorithms.algorithm_runner import AlgorithmRunner


class LoadFiles(QtWidgets.QDialog, Ui_LoadFilesDialogBase):

    def __init__(self, project: QgsProject, parent=None):
        """Constructor."""
        super(LoadFiles, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Load trial files")
        self.layerService = LayerService()
        self.systemService = SystemService()
        self.project = project
        self.crsOperations = ''
        self.pointLayer = ''
        self.pointLayerName = ''
        self.filePath = str()
        self.crsWarningLabel.hide()
        self.progressBar.hide()
        self.suggestedCrsSelectionWidget.setEnabled(False)
        self.reprojectCheckBox.stateChanged.connect(self.layerReprojectWidget)
        self.pointsFileWidget.fileChanged.connect(self.updateGui)
        self.loadPointsPushButton.clicked.connect(self.loadPoints)

    def updateGui(self, path: str) -> None:
        if path:
            self.filePath = path
            self.pointLayerName = self.systemService.extractFileName(path)
            self.pointLayer = self.layerService.createVectorLayer(self.pointLayerName, path)

            if self.pointLayer.crs().isGeographic():
                self.crsWarningLabel.show()
                crsInfo = self.layerService.getSuggestedCrs(self.pointLayer)
                self.crsOperations = crsInfo
                self.suggestedCrsSelectionWidget.setCrs(QgsCoordinateReferenceSystem(crsInfo[2]))
            else:
                self.crsWarningLabel.hide()
                self.suggestedCrsSelectionWidget.setCrs(self.pointLayer.crs())

            self.crsLabel.setText(f'CRS -> {self.pointLayer.crs().authid()}')

    def loadPoints(self):
        filePath = self.project.homePath()
        epsg = self.suggestedCrsSelectionWidget.crs()

        self.layerService.createLayersTreeGroup(self.project)

        if self.reprojectCheckBox.isChecked():

            reprojectedLayerName = f'{self.pointLayerName}_{self.crsOperations[1]}'
            pointLayer = ''
            if not LayerService.checkLayerGeometry(self.pointLayer):
                feedback = UserFeedback()
                pointLayer = AlgorithmRunner.runDropMZValues(self.pointLayer, feedback=feedback)
                feedback.close()

            outputGpsLayer = f"{filePath}/00_Data/00_Raw_Files/{self.pointLayerName}.shp"
            if self.systemService.fileExist(outputGpsLayer) != 65536:
                self.layerService.saveVectorLayer(pointLayer, outputGpsLayer)
                self.layerService.loadShapeFile(QGIS_TOC_GROUPS[0], outputGpsLayer)

            outputReprojectLayer = f"{filePath}/00_Data/01_Reproject/{reprojectedLayerName}.shp"
            if self.systemService.fileExist(outputReprojectLayer) != 65536:
                feedback = UserFeedback()
                AlgorithmRunner.runReprojectLayer(pointLayer, epsg.authid(), self.crsOperations[3],
                                                  feedback=feedback, outputLayer=outputReprojectLayer)
                feedback.close()
                self.layerService.loadShapeFile(QGIS_TOC_GROUPS[1], outputReprojectLayer)

        else:
            outputGpsLayer = f"{filePath}/00_Data/00_Raw_Files/{self.pointLayerName}.shp"
            if self.systemService.fileExist(outputGpsLayer) != 65536:
                self.layerService.saveVectorLayer(self.pointLayer, outputGpsLayer)
                self.layerService.loadShapeFile(QGIS_TOC_GROUPS[0], outputGpsLayer)

        self.clearLoadLayerWidget()

    def layerReprojectWidget(self, state):
        WidgetService.enableWidget(self.suggestedCrsSelectionWidget, state)

    def clearLoadLayerWidget(self):
        widgets = [self.pointsFileWidget,
                   self.crsLabel,
                   self.crsWarningLabel,
                   self.reprojectCheckBox]
        for widget in widgets:
            WidgetService.clearWidget(widget)
