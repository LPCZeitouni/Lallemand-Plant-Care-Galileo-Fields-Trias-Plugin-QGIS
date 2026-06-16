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

from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.gui import QgsOptionsWidgetFactory, QgsOptionsPageWidget

from .options_settings_dlg_base import Ui_Form
from ...core.constants import DEFAULT_SETTINGS

SETTINGS_KEY = "LPC/postgresConnection"


class OptionsSettingsFactory(QgsOptionsWidgetFactory):

    def __init__(self):
        super().__init__()

    def icon(self):
        return QIcon(':plugins/lallemand_plant_care/icons/lallemand.png')

    def createWidget(self, parent=None):
        return OptionsSettingsPage(parent)


class OptionsSettingsPage(QgsOptionsPageWidget, Ui_Form):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.settings = QSettings()
        self.server = DEFAULT_SETTINGS['SERVER']
        self.treatment = DEFAULT_SETTINGS['TREATMENT']
        self.kriging = DEFAULT_SETTINGS['KRIGING']
        self.histogram = DEFAULT_SETTINGS['HISTOGRAM']
        self.symbology = DEFAULT_SETTINGS['SYMBOLOGY']
        self.loadSettings()

    def apply(self):
        self.saveSettings()

    def saveSettings(self):
        self.saveServerSettings()
        self.saveTreatmentPolygonsSettings()
        self.saveKrigingSettings()
        self.saveHistogramSettings()
        self.saveSymbologySettings()
        self.saveSqliteSettings()

    def loadSettings(self):
        self.loadServerSettings()
        self.loadTreatmentPolygonsSettings()
        self.loadKrigingSettings()
        self.loadHistogramSettings()
        self.loadSymbologySettings()
        self.loadSqliteSettings()

    def saveSqliteSettings(self):
        self.settings.setValue('LPC/sqlite', self.sqliteFileWidget.filePath())

    def loadSqliteSettings(self):
        sqlitePath = self.getSqlitePath()
        self.sqliteFileWidget.setFilePath(sqlitePath)

    def getSqliteSettings(self):
        return self.settings.value('LPC/sqlite')

    def saveServerSettings(self):
        self.settings.setValue('LPC/database', self.databaseNameLineEdit.text())
        self.settings.setValue('LPC/host', self.serverIpLineEdit.text())
        self.settings.setValue('LPC/port', self.serverPortLineEdit.text())
        self.settings.setValue('LPC/user', self.serverUserLineEdit.text())
        self.settings.setValue('LPC/password', self.serverPasswordLineEdit.text())

    def loadServerSettings(self):
        self.databaseNameLineEdit.setText(self.settings.value('LPC/database', self.server[0]))
        self.serverIpLineEdit.setText(self.settings.value('LPC/host', self.server[1]))
        self.serverPortLineEdit.setText(self.settings.value('LPC/port', self.server[2]))
        self.serverUserLineEdit.setText(self.settings.value('LPC/user', self.server[3]))
        self.serverPasswordLineEdit.setText(self.settings.value('LPC/password', self.server[4]))

    def getServerSettings(self):
        return {
            'database': self.settings.value('LPC/database'),
            'host': self.settings.value('LPC/host'),
            'port': self.settings.value('LPC/port'),
            'user': self.settings.value('LPC/user'),
            'password': self.settings.value('LPC/password')
        }

    def saveTreatmentPolygonsSettings(self):
        self.settings.setValue('LPC/boucle_rang', self.boucleRadioButton.isChecked())
        self.settings.setValue('LPC/ligne_parcelle', self.ligneRadioButton.isChecked())
        self.settings.setValue('LPC/odd_polygons', self.oddPolygonsNameLineEdit.text())
        self.settings.setValue('LPC/even_polygons', self.evenPolygonsNameLineEdit.text())
        self.settings.setValue('LPC/border_size', self.sizeBorderSpinBox.value())
        self.settings.setValue('LPC/largeur_coupe', self.largeurCoupeSpinBox.value())
        self.settings.setValue('LPC/sous_echantillonnage', self.sousEchantillonnageSpinBox.value())

    def loadTreatmentPolygonsSettings(self):
        self.boucleRadioButton.setChecked(bool(self.settings.value('LPC/boucle_rang', self.treatment[0])))
        self.ligneRadioButton.setChecked(bool(self.settings.value('LPC/ligne_parcelle', self.treatment[1])))
        self.oddPolygonsNameLineEdit.setText(self.settings.value('LPC/odd_polygons', self.treatment[2]))
        self.evenPolygonsNameLineEdit.setText(self.settings.value('LPC/even_polygons', self.treatment[3]))
        self.sizeBorderSpinBox.setValue(float(self.settings.value('LPC/border_size', self.treatment[4])))
        self.largeurCoupeSpinBox.setValue(float(self.settings.value('LPC/largeur_coupe', self.treatment[5])))
        self.sousEchantillonnageSpinBox.setValue(
            float(self.settings.value('LPC/sous_echantillonnage', self.treatment[6])))

    def getTreatmentPolygonsSettings(self):
        return (
            [self.settings.value('LPC/odd_polygons'), self.settings.value('LPC/even_polygons')],
            self.settings.value('LPC/largeur_coupe'),
            self.settings.value('LPC/sous_echantillonnage'),
            self.settings.value('LPC/border_size'),
            [self.settings.value('LPC/boucle_rang'), self.settings.value('LPC/ligne_parcelle')]
        )

    def saveKrigingSettings(self):
        self.settings.setValue('LPC/field_interpolate', self.fieldToInterpolateLineEdit.text())
        self.settings.setValue('LPC/pixel_size_x', self.pixelSizeXSpinBox.value())
        self.settings.setValue('LPC/pixel_size_y', self.pixelSizeYSpinBox.value())

    def loadKrigingSettings(self):
        self.fieldToInterpolateLineEdit.setText(self.settings.value('LPC/field_interpolate', self.kriging[0]))
        self.pixelSizeXSpinBox.setValue(float(self.settings.value('LPC/pixel_size_x', self.kriging[1])))
        self.pixelSizeYSpinBox.setValue(float(self.settings.value('LPC/pixel_size_y', self.kriging[2])))

    def getKrigingSettings(self):
        fields = self.settings.value('LPC/field_interpolate')
        pixelX = self.settings.value('LPC/pixel_size_x')
        pixelY = self.settings.value('LPC/pixel_size_y')
        pixelSize = [pixelX, pixelY]
        return fields, pixelSize

    def saveHistogramSettings(self):
        self.settings.setValue('LPC/histogram_bins', self.binsSpinBox.value())
        self.settings.setValue('LPC/histogram_color', self.colorColorButton.color())
        self.settings.setValue('LPC/histogram_edge_color', self.edgeColorButton.color())

    def loadHistogramSettings(self):
        self.binsSpinBox.setValue(int(self.settings.value('LPC/histogram_bins', self.histogram[0])))
        self.colorColorButton.setColor(self.settings.value('LPC/histogram_color', QColor(self.histogram[1])))
        self.edgeColorButton.setColor(self.settings.value('LPC/histogram_edge_color', QColor(self.histogram[2])))

    def getHistogramSettings(self):
        return (
            self.settings.value('LPC/histogram_bins'),
            QColor(self.settings.value('LPC/histogram_color')),
            QColor(self.settings.value('LPC/histogram_edge_color'))
        )

    def saveSymbologySettings(self):
        self.settings.setValue('LPC/symbology_num_classes', self.classesSpinBox.value())
        self.settings.setValue('LPC/symbology_first_color', self.firstColorButton.color())
        self.settings.setValue('LPC/symbology_second_color', self.secondColorButton.color())
        self.settings.setValue('LPC/symbology_third_color', self.thirdColorButton.color())
        self.settings.setValue('LPC/symbology_fourth_color', self.fourthColorButton.color())

    def loadSymbologySettings(self):
        self.classesSpinBox.setValue(int(self.settings.value('LPC/symbology_num_classes', self.symbology[0])))
        self.firstColorButton.setColor(self.settings.value('LPC/symbology_first_color', QColor(self.symbology[1])))
        self.secondColorButton.setColor(self.settings.value('LPC/symbology_second_color', QColor(self.symbology[2])))
        self.thirdColorButton.setColor(self.settings.value('LPC/symbology_third_color', QColor(self.symbology[3])))
        self.fourthColorButton.setColor(self.settings.value('LPC/symbology_fourth_color', QColor(self.symbology[4])))

    def getSymbologySettings(self):
        return (
            self.settings.value('LPC/symbology_num_classes'),
            [QColor(self.settings.value('LPC/symbology_first_color')),
             QColor(self.settings.value('LPC/symbology_second_color')),
             QColor(self.settings.value('LPC/symbology_third_color')),
             QColor(self.settings.value('LPC/symbology_fourth_color'))]
        )

    @staticmethod
    def getSqlitePath():
        currentDirectory = os.path.dirname(__file__)
        parentDirectory = os.path.join(currentDirectory, '..', '..', 'core/resources/BD_GEOSTAT_LPC.sqlite')
        return os.path.normpath(parentDirectory)
