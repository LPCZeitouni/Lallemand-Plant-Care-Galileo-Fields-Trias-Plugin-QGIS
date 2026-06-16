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

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QHeaderView
from qgis.core import QgsProject

from ...core.factories.sqlite_factory import SqliteFactory
from .geostatistics_trial_dlg_base import Ui_Dialog
from ...core.constants import *
from ...core.factories.postgres_factory import PostgresFactory
from ...core.services.layer_service import LayerService
from ...core.services.message_service import MessageService
from ...core.services.system_service import SystemService
from ...core.services.widget_service import WidgetService


class GeostatisticsTrial(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        """Constructor."""
        super(GeostatisticsTrial, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Geostatistics Trial Information")
        self.project = ''
        self.layer_services = LayerService()
        self.databaseFactory = SqliteFactory()
        self.setTrialWidget()
        self.loadTrialData()
        self.fetchDomain()
        self.fetchLpcTeam()
        self.fetchCropData()
        self.fetchFarmerData()

        self.trialAddPushButton.clicked.connect(self.register)
        self.trialEditPushButton.clicked.connect(self.updateTrialWidget)
        self.trialDeletePushButton.clicked.connect(self.deleteTrial)

    def setTrialWidget(self):
        self.trialTableWidget.setHorizontalHeaderLabels(GEOSTATISTIC_TRIAL)
        self.trialTableWidget.verticalHeader().setVisible(True)
        self.trialTableWidget.setColumnHidden(0, True)
        self.trialTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.trialTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.trialIDLabel.hide()

        WidgetService().floatValidator(self.trialFieldAreaLineEdit)

    def updateTrialWidget(self):
        selectedData = WidgetService.getSelectedData(self.trialTableWidget, 11, 'Updating data')

        if selectedData:
            currentRow, data = selectedData
            self.geostatisticsTrialGroupBox.setTitle('Update trial')
            self.trialIDLabel.setText(data[0])
            self.trialFieldNameLineEdit.setText(data[1])
            self.trialFieldAreaLineEdit.setText(data[2])
            self.trialIrrigatedComboBox.setCurrentIndex(self.trialIrrigatedComboBox.findText(data[3]))
            self.trialSoilTypeLineEdit.setText(data[4])
            self.lpcTeamComboBox.setCurrentIndex(self.lpcTeamComboBox.findText(data[5]))
            self.farmerComboBox.setCurrentIndex(self.farmerComboBox.findText(data[6]))
            self.cropFieldComboBox.setCurrentIndex(self.cropFieldComboBox.findText(data[7]))
            self.trialAddPushButton.setText('Update')
        else:
            MessageService().messageBox('Updating data', 'No data selected.', 5, 1)

    def clearTrialWidget(self):
        self.trialIDLabel.setText('noid')
        self.trialFieldNameLineEdit.clear()
        self.trialFieldAreaLineEdit.clear()
        self.trialSoilTypeLineEdit.clear()
        self.lpcTeamComboBox.setCurrentIndex(0)
        self.farmerComboBox.setCurrentIndex(0)
        self.cropFieldComboBox.setCurrentIndex(0)

    def register(self):
        # TODO move register to the factory
        # connection = PostgresFactory().openConnection('BD_GEOSTAT_LPC')
        buttonType = self.trialAddPushButton.text()

        if buttonType == 'Update':
            sql = UPDATE_TRIAL_SQL
            data = self.prepareTrialData()
            self.trialAddPushButton.setText('Add')
            self.geostatisticsTrialGroupBox.setTitle('Add crop')
            self.trialIDLabel.setText('noid')
        else:
            sql = INSERT_TRIAL_SQL
            data = self.prepareTrialData()

        result = self.databaseFactory.postSqlExecutor(sql, data)
        self.loadTrialData()
        self.clearTrialWidget()
        MessageService().resultMessage(result, 'Trial management', 'Data saved successfully!')

    def deleteTrial(self):
        selectedData = WidgetService.getSelectedData(self.trialTableWidget, 11, 'Deleting data')

        if selectedData:
            currentRow, data = selectedData

            reply = QtWidgets.QMessageBox.question(self, 'Confirmation', 'Are you sure you want to delete this trial?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                result = self.databaseFactory.postSqlExecutor(DELETE_TRIAL_SQL.format(data[0]))
                self.loadTrialData()
                MessageService().resultMessage(result, 'Deleting data', 'Data deleted successfully!')
        else:
            MessageService().messageBox('Deleting data', 'No data selected.', 5, 1)

    def prepareTrialData(self):
        teamId = self.lpcTeamComboBox.itemData(self.lpcTeamComboBox.currentIndex())
        farmerId = self.farmerComboBox.itemData(self.farmerComboBox.currentIndex())
        cropId = self.cropFieldComboBox.itemData(self.cropFieldComboBox.currentIndex())
        irrigated = self.trialIrrigatedComboBox.itemData(self.trialIrrigatedComboBox.currentIndex())

        trialData = [
            self.trialFieldNameLineEdit.text(),
            self.trialFieldAreaLineEdit.text(),
            self.trialIrrigatedComboBox.currentText(),
            self.trialSoilTypeLineEdit.text(),
            teamId,
            farmerId,
            cropId,
            15,
            SystemService().createDate()
        ]
        if self.trialIDLabel.text() != 'noid':
            trialData.append(self.trialIDLabel.text())

        return tuple(trialData)

    def loadTrialData(self):
        result = self.databaseFactory.getSqlExecutor(FETCH_ALL_TRIAL, dictionary=True)
        if len(result) > 0:
            self.tableDataFormatter(result)
        else:
            WidgetService().populateSqliteTable(result, self.trialTableWidget)

    def tableDataFormatter(self, result):
        result_list = list()
        for row in result:
            lpcTeamName = self.databaseFactory.fetchOne(FETCH_ONE_TEAM, row['lpc_team_id'], dictionary=True)
            farmer = self.databaseFactory.fetchOne(FETCH_ONE_FARMER, row['farmer_id'], dictionary=True)
            crop = self.databaseFactory.fetchOne(FETCH_ONE_CROP, row['crop_trial_id'], dictionary=True)
            new_result = dict()
            new_result['id'] = row['id']
            new_result['field_name'] = row['field_name']
            new_result['field_area'] = row['field_area']
            new_result['field_irrigation'] = row['field_irrigation']
            new_result['field_soil'] = row['field_soil']
            new_result['lpc_team'] = f"{lpcTeamName[0]['first_name']} {lpcTeamName[0]['last_name']}"
            new_result['farmer'] = f"{farmer[0]['first_name']} {farmer[0]['last_name']}"
            new_result['crop_trial'] = f"{crop[0]['crop_name']} - {crop[0]['variety']}"
            new_result['id_contour'] = row['id_contour']
            new_result['create_date'] = row['create_date']
            new_result['update_date'] = row['update_date']
            result_list.append(new_result)

        WidgetService().populateTable(result_list, self.trialTableWidget)

    def fetchDomain(self):
        comboboxData = self.databaseFactory.fetchDataToCombobox(self.trialIrrigatedComboBox, FETCH_ALL_DOMAIN,
                                                                ['description'], 'code')
        if not comboboxData[0]:
            MessageService().messageBox('QGIS project', comboboxData[1], 5, 1)

    def fetchLpcTeam(self):
        comboboxData = self.databaseFactory.fetchDataToCombobox(self.lpcTeamComboBox, FETCH_ALL_TEAM,
                                                                ['first_name', 'last_name'], 'id')
        if not comboboxData[0]:
            MessageService().messageBox('QGIS project', comboboxData[1], 5, 1)

    def fetchCropData(self):
        comboboxData = self.databaseFactory.fetchDataToCombobox(self.cropFieldComboBox, FETCH_ALL_CROP,
                                                                ['crop_name', 'variety'], 'id', ' - ')
        if not comboboxData[0]:
            MessageService().messageBox('QGIS project', comboboxData[1], 5, 1)

    def fetchFarmerData(self):
        comboboxData = self.databaseFactory.fetchDataToCombobox(self.farmerComboBox, FETCH_ALL_FARMER,
                                                                ['first_name', 'last_name'], 'id')
        if not comboboxData[0]:
            MessageService().messageBox('QGIS project', comboboxData[1], 5, 1)
