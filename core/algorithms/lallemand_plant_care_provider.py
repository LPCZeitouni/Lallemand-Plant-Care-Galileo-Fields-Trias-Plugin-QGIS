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
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .analysis.create_gain_surface_algorithm import GainSurfaceProcessingAlgorithm
from .analysis.create_sample_layers_algorithm import CreateSampleLayersProcessingAlgorithm
from .analysis.error_compensation_algorithm import ErrorCompensationProcessingAlgorithm
from .analysis.filter_treatments_algorithm import FilterTreatmentProcessingAlgorithm
from .analysis.simple_sampling_algorithm import SamplingProcessingAlgorithm
from .vector.filtering_harvester_points_algorithm import FilteringHarvesterPointsProcessingAlgorithm
from .vector.treatment_polygon_builder_algorithm import TreatmentPolygonsBuilderProcessingAlgorithm
from .graphs.histogram_graph_algorithm import HistogramGraphProcessingAlgorithm
from .rmse.calculate_error_algorithm import CalculateErrorProcessingAlgorithm
from .maps.export_maps_algorithm import ExportMapsProcessingAlgorithm
from .maps.load_composer_templates import LoadComposerTemplatesAlgorithm
from .report.presentation_algorithm import PresentationProcessingAlgorithm
from .report.report_algorithm import ReportProcessingAlgorithm
from .rmse.rmse_algorithm import RMSEProcessingAlgorithm


class LPCAlgorithmProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(FilterTreatmentProcessingAlgorithm())
        self.addAlgorithm(SamplingProcessingAlgorithm())
        self.addAlgorithm(CreateSampleLayersProcessingAlgorithm())
        self.addAlgorithm(ErrorCompensationProcessingAlgorithm())
        self.addAlgorithm(GainSurfaceProcessingAlgorithm())
        self.addAlgorithm(TreatmentPolygonsBuilderProcessingAlgorithm())
        self.addAlgorithm(FilteringHarvesterPointsProcessingAlgorithm())
        self.addAlgorithm(RMSEProcessingAlgorithm())
        self.addAlgorithm(CalculateErrorProcessingAlgorithm())
        self.addAlgorithm(HistogramGraphProcessingAlgorithm())
        self.addAlgorithm(ReportProcessingAlgorithm())
        self.addAlgorithm(PresentationProcessingAlgorithm())
        self.addAlgorithm(ExportMapsProcessingAlgorithm())
        self.addAlgorithm(LoadComposerTemplatesAlgorithm())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'lpc'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('Lallemand Plant Care')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/icons/icon.png')

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
