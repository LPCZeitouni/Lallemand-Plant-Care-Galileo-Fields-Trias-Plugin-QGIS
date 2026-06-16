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

from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtWidgets import QHeaderView

from .farmer_manager_dlg_base import Ui_FarmerDialog
from ...core.constants import *
from ...core.factories.sqlite_factory import SqliteFactory
from ...core.services.message_service import MessageService
from ...core.services.system_service import SystemService
from ...core.services.widget_service import WidgetService


class FarmerManager(QtWidgets.QDialog, Ui_FarmerDialog):

    def __init__(self):
        """Constructor."""
        super(FarmerManager, self).__init__()
        self.setupUi(self)
        self.databaseFactory = SqliteFactory()
        self.setWindowTitle("Farmer and Crop Management")
        self.setFarmerWidget()
        self.setCropWidget()
        self.loadCropData()
        self.loadFarmerData()

        self.farmerAddPushButton.clicked.connect(self.registerFarmer)
        self.cropAddPushButton.clicked.connect(self.registerCrop)
        self.farmerDeletePushButton.clicked.connect(self.deleteFarmer)
        self.cropDeletePushButton.clicked.connect(self.deleteCrop)
        self.cropEditPushButton.clicked.connect(self.updateCropWidget)
        self.farmerEditPushButton.clicked.connect(self.updateFarmerWidget)

    def setFarmerWidget(self):
        self.farmerTableWidget.setHorizontalHeaderLabels(FARMER_COLUMN_NAMES)
        self.farmerTableWidget.setColumnHidden(0, True)
        self.farmerTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.farmerTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.farmerIDLabel.hide()

    def clearFarmerWidget(self):
        self.farmerFirstNameLineEdit.clear()
        self.farmerLastNameLineEdit.clear()
        self.farmerAddressLineEdit.clear()
        self.farmerTown.clear()
        self.farmerCountry.clear()
        self.farmerZipCode.clear()

    def updateFarmerWidget(self):
        selectedData = WidgetService.getSelectedData(self.farmerTableWidget, 9, 'Updating data')

        if selectedData:
            currentRow, data = selectedData
            self.farmerGroupBox.setTitle('Update farmer')
            self.farmerIDLabel.setText(data[0])
            self.farmerFirstNameLineEdit.setText(data[1])
            self.farmerLastNameLineEdit.setText(data[2])
            self.farmerAddressLineEdit.setText(data[3])
            self.farmerTown.setText(data[5])
            self.farmerCountry.setText(data[6])
            self.farmerZipCode.setText(data[4])
            self.farmerAddPushButton.setText('Update')
        else:
            MessageService().messageBox('Updating data', 'No data selected.', 5, 1)

    def setCropWidget(self):
        self.cropTableWidget.setHorizontalHeaderLabels(CROP_COLUMN_NAMES)
        self.cropTableWidget.setColumnHidden(0, True)
        self.cropTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.cropTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.cropSowingDate.setDateTime(QtCore.QDateTime.currentDateTime())
        self.cropHarvestingDate.setDateTime(QtCore.QDateTime.currentDateTime())
        self.cropIDLabel.hide()

    def clearCropWidget(self):
        self.cropNameLineEdit.clear()
        self.cropSowingDate.setDateTime(QtCore.QDateTime.currentDateTime())
        self.cropHarvestingDate.setDateTime(QtCore.QDateTime.currentDateTime())
        self.cropVarietyLineEdit.clear()
        self.cropInterRoCMSpinBox.setValue(float(0))

    def updateCropWidget(self):
        selectedData = WidgetService.getSelectedData(self.cropTableWidget, 8, 'Updating data')

        if selectedData:
            currentRow, data = selectedData
            self.registerCropGroupBox.setTitle('Update crop')
            self.cropIDLabel.setText(data[0])
            self.cropNameLineEdit.setText(data[1])
            self.cropSowingDate.setDate(QtCore.QDate.fromString(data[2], 'yyyy-MM-dd'))
            self.cropHarvestingDate.setDate(QtCore.QDate.fromString(data[3], 'yyyy-MM-dd'))
            self.cropVarietyLineEdit.setText(data[4])
            self.cropInterRoCMSpinBox.setValue(float(data[5]))
            self.cropAddPushButton.setText('Update')
        else:
            MessageService().messageBox('Updating data', 'No data selected.', 5, 1)

    def registerCrop(self):
        self.register('crop')

    def registerFarmer(self):
        self.register('farmer')

    def register(self, registerType):

        if registerType == 'crop':
            buttonType = self.cropAddPushButton.text()

            if buttonType == 'Update':
                sql = UPDATE_CROP_SQL
                data = self.prepareCropData()
                self.cropAddPushButton.setText('Add')
                self.registerCropGroupBox.setTitle('Add crop')
                self.cropIDLabel.setText('noid')
            else:
                sql = INSERT_CROP_SQL
                data = self.prepareCropData()

            result = self.databaseFactory.postSqlExecutor(sql, data)
            self.loadCropData()
            self.clearCropWidget()
            MessageService().resultMessage(result, 'Crop field management', 'Data saved successfully!')

        elif registerType == 'farmer':
            buttonType = self.farmerAddPushButton.text()

            if buttonType == 'Update':
                sql = UPDATE_FARMER_SQL
                data = self.prepareFarmerData()
                self.farmerAddPushButton.setText('Add')
                self.farmerGroupBox.setTitle('Add farmer')
                self.farmerIDLabel.setText('noid')
            else:
                sql = INSERT_FARMER_SQL
                data = self.prepareFarmerData()

            result = self.databaseFactory.postSqlExecutor(sql, data)

            self.loadFarmerData()
            self.clearFarmerWidget()

            MessageService().resultMessage(result, 'Farmer management', 'Data saved successfully!')

    def prepareCropData(self):
        cropData = [self.cropNameLineEdit.text(),
                    self.cropSowingDate.date().toPyDate().strftime('%Y-%m-%d'),
                    self.cropHarvestingDate.date().toPyDate().strftime('%Y-%m-%d'),
                    self.cropVarietyLineEdit.text(),
                    self.cropInterRoCMSpinBox.value(),
                    SystemService().createDate()]

        if self.cropIDLabel.text() != 'noid':
            cropData.append(self.cropIDLabel.text())

        return tuple(cropData)

    def prepareFarmerData(self):
        farmerData = [self.farmerFirstNameLineEdit.text(),
                      self.farmerLastNameLineEdit.text(),
                      self.farmerAddressLineEdit.text(),
                      self.farmerZipCode.text(),
                      self.farmerTown.text(),
                      self.farmerCountry.text(),
                      SystemService().createDate()]

        if self.farmerIDLabel.text() != 'noid':
            farmerData.append(self.farmerIDLabel.text())
        return tuple(farmerData)

    def loadCropData(self):
        result = self.databaseFactory.getSqlExecutor(FETCH_ALL_CROP)

        WidgetService().populateSqliteTable(result, self.cropTableWidget)

    def loadFarmerData(self):
        result = self.databaseFactory.getSqlExecutor(FETCH_ALL_FARMER)

        WidgetService().populateSqliteTable(result, self.farmerTableWidget)

    def deleteFarmer(self):
        selectedData = WidgetService().getSelectedData(self.farmerTableWidget, 9, 'Deleting data')

        if selectedData:
            currentRow, data = selectedData
            trial = self.databaseFactory.fetchOne(FETCH_TRIAL_FARMER, data[0], dictionary=True)

            if len(trial) > 0:
                MessageService().messageBox('Deleting data', 'There is a trial related to this farmer.', 5, 1)
                return

            reply = QtWidgets.QMessageBox.question(self, 'Confirmation', 'Are you sure you want to delete this farmer?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                result = self.databaseFactory.postSqlExecutor(DELETE_FARMER_SQL.format(data[0]))
                self.loadFarmerData()
                MessageService().resultMessage(result, 'Farmer management', 'Data deleted successfully!')
        else:
            MessageService().messageBox('Deleting data', 'No data selected.', 5, 1)

    def deleteCrop(self):
        selectedData = WidgetService.getSelectedData(self.cropTableWidget, 8, 'Deleting data')

        if selectedData:
            currentRow, data = selectedData
            trial = self.databaseFactory.fetchOne(FETCH_TRIAL_CROP, data[0], dictionary=True)

            if len(trial) > 0:
                MessageService().messageBox('Deleting data', 'There is a trial related to this crop.', 5, 1)
                return

            reply = QtWidgets.QMessageBox.question(self, 'Confirmation', 'Are you sure you want to delete this crop?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                result = self.databaseFactory.postSqlExecutor(DELETE_CROP_SQL.format(data[0]))
                self.loadCropData()
                MessageService().resultMessage(result, 'Crop management', 'Data deleted successfully!')
        else:
            MessageService().messageBox('Deleting data', 'No data selected.', 5, 1)
