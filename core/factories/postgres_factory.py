# -*-# -*- coding: utf-8 -*-
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

import psycopg2
import psycopg2.extras
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from ...gui.settings.options_settings_dlg import OptionsSettingsPage


class PostgresFactory:
    def __init__(self):
        super(PostgresFactory, self).__init__()
        self.settings = OptionsSettingsPage().getServerSettings()
        self._initializeLogging()
        # self.connection = self.openConnection()

    @staticmethod
    def _initializeLogging():
        logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), 'postgres_log.log'), level=logging.ERROR)

    def openConnection(self):
        with psycopg2.connect(
            database=self.settings['database'],
            user=self.settings['user'],
            password=self.settings['password'],
            host=self.settings['host'],
            port=self.settings['port']
        ) as connection:
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            connection.autocommit = True
        return connection

    def fetchDataToCombobox(self, combobox, query, displayColumns, idColumn, concatSeparator=' '):
        try:
            combobox.clear()
            result = self.getSqlExecutor(query)

            for row in result:
                displayValue = concatSeparator.join([str(row[column]) for column in displayColumns])
                combobox.addItem(displayValue, row[idColumn])

            return True, combobox

        except Exception as e:
            errorMessage = f"Error executing SQL query: {str(e)}"
            return False, errorMessage

    def fetchOne(self, baseSql, objectId):
        objectSql = baseSql.format(objectId)
        return self.getSqlExecutor(objectSql)

    def getSqlExecutor(self, sql):
        try:
            connection = self.openConnection()
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as curs:
                curs.execute(sql)
                result = curs.fetchall()
            return result

        except psycopg2.Error as e:
            error_message = f"Error executing SQL: {e}"
            logging.error(error_message)
            return error_message

    def postSqlExecutor(self, sql, data=None):
        try:
            connection = self.openConnection()
            with connection.cursor() as curs:
                if data:
                    curs.execute(sql, data)
                else:
                    curs.execute(sql)
            return True

        except psycopg2.Error as e:
            error_message = f"Error executing SQL: {e}"
            logging.error(error_message)
            return False, error_message

    @staticmethod
    def close_connection(connection):
        connection.close()
