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
from qgis.PyQt.QtWidgets import QHeaderView

from .team_manager_dlg_base import Ui_LpcTeamManagerDialog
from ...core.constants import FETCH_ALL_TEAM, DELETE_TEAM_SQL, UPDATE_TEAM_SQL, INSERT_TEAM_SQL, FETCH_ONE_TEAM, \
    FETCH_ONE_TRIAL, FETCH_TRIAL_TEAM
from ...core.factories.sqlite_factory import SqliteFactory
from ...core.services.message_service import MessageService
from ...core.services.system_service import SystemService
from ...core.services.widget_service import WidgetService


class RegisterLpcTeam(QtWidgets.QDialog, Ui_LpcTeamManagerDialog):

    def __init__(self):
        """Constructor."""
        super(RegisterLpcTeam, self).__init__()
        self.setupUi(self)
        self.databaseFactory = SqliteFactory()
        self.widgetService = WidgetService()
        self.messageService = MessageService()
        self.setWindowTitle("LPC Team Management")
        self.tableWidget.setHorizontalHeaderLabels(['Id', "First name", "Last name", "Create date"])
        self.tableWidget.setColumnHidden(0, True)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.lpcTeamIDLabel.hide()
        self.lpcTeamAddPushButton.clicked.connect(self.validateEntries)
        self.deletePushButton.clicked.connect(self.deleteTeamMember)
        self.editPushButton.clicked.connect(self.updateTeamWidget)
        self.loadData()

    def validateEntries(self):
        if self.lpcTeamFirstNameLineEdit.text() == '' or self.lpcTeamLastNameLineEdit.text() == '':
            self.messageService.criticalMessage('LPC Team Management', 'There are empty fields!')
            return

        self.register()

    def register(self):
        buttonType = self.lpcTeamAddPushButton.text()

        if buttonType == 'Update':
            sql = UPDATE_TEAM_SQL
            data = self.prepareTeamData()
            self.lpcTeamAddPushButton.setText('Add')
            self.addGroupBox.setTitle('Add professional')
            self.lpcTeamIDLabel.setText('noid')
        else:
            sql = INSERT_TEAM_SQL
            data = self.prepareTeamData()

        result = self.databaseFactory.postSqlExecutor(sql, data)

        self.loadData()
        self.lpcTeamLastNameLineEdit.clear()
        self.lpcTeamFirstNameLineEdit.clear()

        self.messageService.resultMessage(result, 'LPC Team Management', 'Data saved successfully!')

    def prepareTeamData(self):

        trialData = [
            self.lpcTeamFirstNameLineEdit.text(),
            self.lpcTeamLastNameLineEdit.text(),
            SystemService().createDate()
        ]
        if self.lpcTeamIDLabel.text() != 'noid':
            trialData.append(self.lpcTeamIDLabel.text())

        return tuple(trialData)

    def loadData(self):
        result = self.databaseFactory.getSqlExecutor(FETCH_ALL_TEAM)
        WidgetService().populateSqliteTable(result, self.tableWidget)

    def deleteTeamMember(self):
        selectedData = WidgetService().getSelectedData(self.tableWidget, 5, 'Deleting data')

        if selectedData:
            currentRow, data = selectedData
            trial = self.databaseFactory.fetchOne(FETCH_TRIAL_TEAM, data[0], dictionary=True)

            if len(trial) > 0:
                MessageService().messageBox('Deleting data', 'There is a trial related to this professional.', 5, 1)
                return

            reply = QtWidgets.QMessageBox.question(self, 'Confirmation', 'Are you sure you want to delete this member?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                result = self.databaseFactory.postSqlExecutor(DELETE_TEAM_SQL.format(data[0]))
                self.loadData()
                MessageService().resultMessage(result, 'Deleting data', 'Data deleted successfully!')
        else:
            MessageService().messageBox('Deleting data', 'No data selected.', 5, 1)

    def updateTeamWidget(self):
        selectedData = WidgetService().getSelectedData(self.tableWidget, 5, 'Updating data')

        if selectedData:
            currentRow, data = selectedData
            self.lpcTeamFirstNameLineEdit.setText(data[1])
            self.lpcTeamLastNameLineEdit.setText(data[2])
            self.lpcTeamAddPushButton.setText('Update')
            self.addGroupBox.setTitle('Update professional')
            self.lpcTeamIDLabel.setText(data[0])
        else:
            MessageService().messageBox('Updating data', 'No data selected.', 5, 1)
