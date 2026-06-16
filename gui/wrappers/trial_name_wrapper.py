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

from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt import QtWidgets
from qgis.core import (QgsProcessingParameterDefinition)

from ...core.constants import FETCH_ALL_TRIAL
from ...core.factories.postgres_factory import PostgresFactory
from ...core.factories.sqlite_factory import SqliteFactory


class TrialNameWidgetWrapper(WidgetWrapper):
    def __init__(self, *args, **kwargs):
        super(TrialNameWidgetWrapper, self).__init__(*args, **kwargs)

    def createWidget(self):
        self.trialComboBox = QtWidgets.QComboBox()
        SqliteFactory().fetchDataToCombobox(self.trialComboBox, 'SELECT * FROM geostatistic_trial', ['field_name'], 'id')
        self.trialComboBox.dialogType = self.dialogType
        self.trialComboBox.setEditable(True)
        return self.trialComboBox

    def parentLayerChanged(self, layer=None):
        pass

    def setLayer(self, layer):
        pass

    def setValue(self, value):
        pass

    def value(self):
        return self.trialComboBox.itemData(self.trialComboBox.currentIndex())

    def postInitialize(self, wrappers):
        pass


class ParameterTrialName(QgsProcessingParameterDefinition):
    def __init__(self, name, description=""):
        super().__init__(name, description)

    def clone(self):
        copy = ParameterTrialName(self.name(), self.description())
        return copy

    def type(self):
        return self.typeName()

    @staticmethod
    def typeName():
        return "trialname"

    def checkValueIsAcceptable(self, value, context=None):
        return True

    def metadata(self):
        return {
            "widget_wrapper": "lallemand_plant_care.gui.wrappers.trial_name_wrapper.TrialNameWidgetWrapper"
        }

    def valueAsPythonString(self, value, context):
        return str(value)

    def asScriptCode(self):
        raise NotImplementedError()

    @classmethod
    def fromScriptCode(cls, name, description, isOptional, definition):
        raise NotImplementedError()
