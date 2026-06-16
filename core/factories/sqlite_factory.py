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

import sqlite3
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from ..services.layer_service import LayerService
from ...gui.settings.options_settings_dlg import OptionsSettingsPage


class SqliteFactory:
    def __init__(self):
        super(SqliteFactory, self).__init__()
        self._initializeLogging()

    @staticmethod
    def _initializeLogging():
        logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), 'sqlite_log.log'), level=logging.ERROR)

    @staticmethod
    def openConnection():
        sqliteDatabase = OptionsSettingsPage().getSqliteSettings()
        if not sqliteDatabase:
            # Caminho “padrão” na mesma pasta do sqlite_factory.py
            sqliteDatabase = os.path.join(os.path.dirname(__file__), "default_db.sqlite")

        return sqlite3.connect(sqliteDatabase)

    def fetchDataToCombobox(self, combobox, query, displayColumns, idColumn, concatSeparator=' '):
        try:
            combobox.clear()
            result = self.getSqlExecutor(query, dictionary=True)

            for row in result:
                displayValue = concatSeparator.join([str(row[column]) for column in displayColumns])
                combobox.addItem(displayValue, row[idColumn])

            return True, combobox

        except Exception as e:
            errorMessage = f"Error executing SQL query: {str(e)}"
            return False, errorMessage

    def fetchOne(self, baseSql, objectId, dictionary=False):
        objectSql = baseSql.format(objectId)
        return self.getSqlExecutor(objectSql, dictionary=dictionary)

    def getSqlExecutor(self, sql, dictionary=False):
        try:
            connection = self.openConnection()
            if dictionary:
                connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            result = cursor.execute(sql)

            return result.fetchall()

        except sqlite3.Error as e:
            error_message = f"Error executing SQL: {e}"
            logging.error(error_message)
            return error_message

    def postSqlExecutor(self, sql, data=None):
        try:
            connection = self.openConnection()
            curs = connection.cursor()
            if data:
                curs.execute(sql, data)
                connection.commit()
            else:
                curs.execute(sql)
                connection.commit()
            return True

        except sqlite3.Error as e:
            error_message = f"Error executing SQL: {e}"
            logging.error(error_message)
            return False, error_message

    @staticmethod
    def close_connection(connection):
        connection.close()
