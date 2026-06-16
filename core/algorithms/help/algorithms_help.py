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


import json
import os


class ProcessingAlgorithmHelpCreator(object):

    @staticmethod
    def shortHelpString(algorithm_name):
        name = algorithm_name.split('_')
        algorithmName = name[0] + ''.join(word for word in name[1:])
        html_path = "{}/{}.html".format(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html'), algorithmName)

        html_file = open(html_path, "r")
        html_string = html_file.read()

        return html_string
