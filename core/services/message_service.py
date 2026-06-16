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
from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
from qgis.core import Qgis, QgsProcessingFeedback, QgsMessageLog


class MessageService:
    def __init__(self, iface=None):
        self.iface = iface
        self.pluginName = self._tr('Lallemand Plant Care')

    @staticmethod
    def _tr(string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('MessageService', string)

    @staticmethod
    def warningMessage(title, message):
        return QMessageBox.warning(None, title, message, QMessageBox.Ok)

    @staticmethod
    def questionMessage(title, message):
        return QMessageBox.question(None, title, message, QMessageBox.Ok)

    @staticmethod
    def informationMessage(title, message):
        return QMessageBox.information(None, title, message, QMessageBox.Ok)

    def informationMessageBar(self, title, message):
        self.iface.messageBar().pushMessage(
            self._tr(title), self._tr(message), level=Qgis.Info, duration=5)

    @staticmethod
    def criticalMessage(title, message):
        return QMessageBox.critical(None, title, message, QMessageBox.Ok)

    def criticalMessageBar(self, title, message):
        self.iface.messageBar().pushMessage(
            self._tr(title), self._tr(message), level=Qgis.Critical, duration=5)

    def logMessage(self, message, level=None):
        if level == 0:
            QgsMessageLog.logMessage(self._tr(message), self.pluginName, level=Qgis.Info)

        elif level == 1:
            QgsMessageLog.logMessage(self._tr(message), self.pluginName, level=Qgis.Warning)

        elif level == 2:
            QgsMessageLog.logMessage(self._tr(message), self.pluginName, level=Qgis.Critical)

        elif level == 3:
            QgsMessageLog.logMessage(self._tr(message), self.pluginName, level=Qgis.Success)

    @staticmethod
    def _setIconType(iconType):
        if iconType == 1:
            return QMessageBox.NoIcon
        elif iconType == 2:
            return QMessageBox.Question
        elif iconType == 3:
            return QMessageBox.Information
        elif iconType == 4:
            return QMessageBox.Warning
        else:
            return QMessageBox.Critical

    @staticmethod
    def _setButtonType(buttonType):
        if buttonType == 1:
            return QMessageBox.Ok
        elif buttonType == 2:
            return QMessageBox.Cancel
        elif buttonType == 3:
            return QMessageBox.Close
        elif buttonType == 4:
            return QMessageBox.Save
        elif buttonType == 5:
            return QMessageBox.Yes
        elif buttonType == 6:
            return QMessageBox.No
        elif buttonType == [1, 2]:
            return QMessageBox.Ok | QMessageBox.Cancel
        elif buttonType == [5, 6]:
            return QMessageBox.Yes | QMessageBox.No

    def resultMessage(self, result, title, message):
        if isinstance(result, bool):
            self.messageBox(title, message, 3, 1)
        else:
            self.messageBox(title, result[1], 5, 1)

    def messageBox(self, title, message, iconType, buttonType):
        messageBox = QMessageBox()
        messageBox.setWindowTitle(self._tr(title))
        messageBox.setIcon(self._setIconType(iconType))
        messageBox.setText(self._tr(message))
        messageBox.setStandardButtons(self._setButtonType(buttonType))
        messageBox.setDefaultButton(self._setButtonType(buttonType))
        choice = messageBox.exec_()
        return choice

    def standardButtonMessage(self, title, message, iconType, buttonType):
        messageBox = QMessageBox()
        messageBox.setWindowTitle(self._tr(title))
        messageBox.setIcon(self._setIconType(iconType))
        messageBox.setText(self._tr(message[0]))
        messageBox.setInformativeText(self._tr(message[1]))
        messageBox.setStandardButtons(self._setButtonType(buttonType))
        messageBox.setDefaultButton(self._setButtonType(buttonType[1]))
        choice = messageBox.exec_()
        return choice

    def saveFileDialog(self):
        fileDialog = QFileDialog()
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        fileDialog.setNameFilter(self._tr("QGIS Project Files (*.qgz *.qgs)"))
        fileDialog.setDefaultSuffix("qgz")
        return fileDialog


class UserFeedback(QgsProcessingFeedback):

    def __init__(self, message=None, title=None, parent=None):
        super(UserFeedback, self).__init__()
        self.title = title
        self.message = message
        self.progressBar = QProgressDialog(self.message, "Cancel", 0, 5, parent)
        self.progressBar.setWindowTitle(self.title)
        self.progressBar.setWindowModality(Qt.WindowModal)

    def setProgress(self, percent):
        self.progressBar.setValue(percent)

    def show(self):
        self.progressBar.show()

    # def pushInfo(self, info):
    #     self.progressBar.setLabelText(info)

    def pushConsoleInfo(self, info):
        self.progressBar.setLabelText(info)

    def pushMessage(self, message, level=0, duration=0):
        self.progressBar.setLabelText(message)

    def isCanceled(self):
        return self.progressBar.wasCanceled()

    def close(self):
        self.progressBar.close()
