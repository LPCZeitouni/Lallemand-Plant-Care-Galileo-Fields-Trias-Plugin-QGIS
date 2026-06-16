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
from typing import Optional

from qgis.PyQt import QtWidgets
from qgis.core import QgsFieldProxyModel, QgsMapLayerProxyModel, QgsTask
from qgis.utils import plugins

from .kriging_dlg_base import Ui_Dialog
from ..settings.options_settings_dlg import OptionsSettingsPage
from ...core.services.layer_service import LayerService
from ...core.services.message_service import MessageService
from ...core.services.system_service import SystemService


class OrdinaryKriging(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, iface, project, parent=None):
        """Constructor."""
        super(OrdinaryKriging, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Ordinary kriging')
        self.iface = iface
        self.project = project
        self.smartMap = ''
        self.filePath = self.project.homePath()
        self.settings = OptionsSettingsPage().getKrigingSettings()
        self.task: Optional[QgsTask] = None
        self.layerService = LayerService()
        self.systemService = SystemService()
        self.filterString = ''
        self.setKrigingGui()
        self.samplingLayerComboBox.layerChanged.connect(self.setFieldName)
        self.interpolatePushButton.clicked.connect(self.runSmartMap)

    def smartMapPluginCheck(self):
        if 'Smart_Map' not in plugins:
            MessageService().messageBox('Plugin check', 'Smart Map plugin is not installed!.', 5, 1)
            return False

        self.smartMap = plugins['Smart_Map']
        return True

    def setFieldName(self):
        name = self.samplingLayerComboBox.currentLayer().name()

        if name in ['T1_validation', 'T2_validation']:
            self.filterString = 'error'
            samplingFields = self.layerService.filterByFieldName(self.samplingLayerComboBox.currentLayer(),
                                                                 [self.filterString], inverse=False)
            self.samplingFieldComboBox.setFields(samplingFields)

        else:
            self.filterString = self.settings[0]
            samplingFields = self.layerService.filterByFieldName(self.samplingLayerComboBox.currentLayer(),
                                                                 self.filterString, inverse=False)
            self.samplingFieldComboBox.setFields(samplingFields)

    def setKrigingGui(self):

        layers = self.project.instance().mapLayers()
        smartMap = self.smartMapPluginCheck()

        if self.samplingLayerComboBox.count() == 0 or not smartMap:
            self.parametersGroupBox.setEnabled(False)
            self.interpolatePushButton.setEnabled(False)

        else:
            boundaryLayer = self.layerService.filterByLayerName(list(layers.values()), ['contour_'])
            samplingLayer = self.layerService.filterByLayerName(list(layers.values()),
                                                                ['Yield_Map_', 'T1_80_perc', 'T2_80_perc', 'T1_total',
                                                                 'T2_total', 'T1_validation', 'T2_validation'],
                                                                )

            self.samplingLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
            self.samplingLayerComboBox.setExceptedLayerList(samplingLayer)

            self.samplingFieldComboBox.setFilters(QgsFieldProxyModel.Numeric)
            self.samplingFieldComboBox.setLayer(self.samplingLayerComboBox.currentLayer())

            self.setFieldName()
            samplingFields = self.layerService.filterByFieldName(self.samplingLayerComboBox.currentLayer(),
                                                                 self.filterString)

            self.samplingFieldComboBox.setFields(samplingFields)

            self.boundaryLayerComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)
            self.boundaryLayerComboBox.setExceptedLayerList(boundaryLayer)

            self.pixelSizeXSpinBox.setValue(float(self.settings[1][0]))
            self.pixelSizeYSpinBox.setValue(float(self.settings[1][1]))

    def getParameters(self):
        return {
            'layer': self.samplingLayerComboBox.currentLayer(),
            'field': self.samplingFieldComboBox.currentField(),
            'pixelSizeX': self.pixelSizeXSpinBox.value(),
            'pixelSizeY': self.pixelSizeYSpinBox.value(),
            'outlinePolygon': self.boundaryLayerComboBox.currentLayer()
        }

    def getPathByLayer(self, layer):
        if 'T1_T2_total' in layer.name():
            return f"{self.filePath}/01_Kriging/01_T1_T2_Total"
        elif 'T1_total' in layer.name():
            return f"{self.filePath}/01_Kriging/02_T1_Total"
        elif 'T1_80' in layer.name():
            return f"{self.filePath}/01_Kriging/04_T1_80perc"
        elif 'T2_total' in layer.name():
            return f"{self.filePath}/01_Kriging/03_T2_Total"
        elif 'T2_80' in layer.name():
            return f"{self.filePath}/01_Kriging/05_T2_80perc"
        elif 'T1_validation' in layer.name():
            return f"{self.filePath}/03_Error_Compensation/T1_Error_Compensation"
        elif 'T2_validation' in layer.name():
            return f"{self.filePath}/03_Error_Compensation/T2_Error_Compensation"

    def runSmartMap(self):
        self.close()
        parameters = self.getParameters()
        path = self.getPathByLayer(parameters['layer'])

        smartMapDialog = self.smartMap.dlg
        self.smartMap.reset_gui()
        smartMapDialog.lineEdit.setText(path)
        self.smartMap.path_absolute = path
        self.smartMap.maximum_points_plugin = 10000

        smartMapDialog.checkBox_Qgis_Raster.setChecked(True)
        smartMapDialog.checkBox_Eliminate_Outilier.setChecked(False)

        smartMapDialog.mMapLayerComboBox.setLayer(parameters['layer'])
        self.smartMap.mMapLayerComboBox_changed()
        smartMapDialog.comboBox_VTarget.setCurrentText(parameters['field'])

        self.smartMap.pushButton_ImportQGIS_clicked()
        self.smartMap.VTarget_FileName = f"{parameters['layer'].name()}_{parameters['field']}"

        smartMapDialog.label_CordX_AreaCont.hide()
        smartMapDialog.label_CordY_AreaCont.hide()
        smartMapDialog.comboBox_CordX_AreaCont.hide()
        smartMapDialog.comboBox_CordY_AreaCont.hide()
        smartMapDialog.datatable_limite.hide()

        smartMapDialog.SpinBox_Pixel_Size_X.setValue(parameters['pixelSizeX'])
        self.smartMap.SpinBox_Pixel_Size_X_changed()
        smartMapDialog.SpinBox_Pixel_Size_Y.setValue(parameters['pixelSizeY'])
        self.smartMap.SpinBox_Pixel_Size_Y_changed()

        smartMapDialog.checkBox_Area_Contorno.setChecked(True)
        self.smartMap.checkBox_Area_Contorno_clicked()
        smartMapDialog.mMapLayerComboBox_AreaCont.setLayer(parameters['outlinePolygon'])
        self.smartMap.mMapLayerComboBox_AreaCont_changed()
        self.smartMap.pushButton_Area_Contorno_clicked()

        self.smartMap.pushButton_VariogramaAjust_clicked()

        # smartMapDialog.tabWidget_Interpolacao_OK.setCurrentIndex(2)
        self.smartMap.pushButton_Krigagem_clicked()

        # smartMapDialog.tabWidget_Interpolacao_OK.setCurrentIndex(3)
        self.smartMap.pushButton_VariogramaSave_clicked()

        # smartMapDialog.tabWidget_Interpolacao_OK.setCurrentIndex(0)
        smartMapDialog.comboBox_Modelo.setCurrentIndex(2)
        self.smartMap.comboBox_Modelo_changed(2)

        self.systemService.copyVariogram(path, f'{self.filePath}/05_Results/02_Variograms')
