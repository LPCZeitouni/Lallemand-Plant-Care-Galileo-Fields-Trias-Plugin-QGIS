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

import processing
from processing import createAlgorithmDialog

from qgis.core import QgsCoordinateReferenceSystem, QgsProcessingUtils, QgsProject
from qgis.PyQt.Qt import QObject

from ..services.layer_service import LayerService


class AlgorithmRunner(QObject):

    def __init__(self):
        super(AlgorithmRunner, self).__init__()
        self.layerService = LayerService()

    @staticmethod
    def _getLayerFromContext(outputDict, context, field=None, returnError=False):
        if field:
            lyr = QgsProcessingUtils.mapLayerFromString(outputDict[field], context)
        else:
            lyr = QgsProcessingUtils.mapLayerFromString(outputDict['Carte_filtree'], context)
        if returnError:
            errorLyr = QgsProcessingUtils.mapLayerFromString(outputDict['error'], context)
            return lyr, errorLyr
        else:
            return lyr

    @staticmethod
    def runWaypointsPolygonsBuilder(layer, method, sorting, sizeBorder, context=None, feedback=None, outputLayer=None):
        outputLayer = 'memory:' if outputLayer is None else outputLayer
        parameters = {
            'Waypoints': layer,
            'Initial_Projection': 0,
            'Reprojection': 0,
            'Methode': method,
            'Variable_ordonnee': sorting,
            'Size_border': sizeBorder,
            'Polygones_traitement': outputLayer
        }
        output = processing.run('r:Waypoints_Polygons_builder_v3_border', parameters, context=context,
                                feedback=feedback)
        return output['Polygones_traitement']

    @staticmethod
    def runReprojectLayer(layer, targetCrs, operation=None, context=None, feedback=None, outputLayer=None):
        outputLayer = 'memory:' if outputLayer is None else outputLayer
        parameters = {
            'INPUT': layer,
            'TARGET_CRS': QgsCoordinateReferenceSystem(targetCrs),
            'OPERATION': operation,
            'OUTPUT': outputLayer
        }
        output = processing.run('native:reprojectlayer', parameters, context=context, feedback=feedback)

        return output['OUTPUT']

    @staticmethod
    def runDropMZValues(layer, context=None, feedback=None, outputLayer=None):
        outputLayer = 'memory:' if outputLayer is None else outputLayer
        parameters = {
            'INPUT': layer,
            'DROP_M_VALUES': True,
            'DROP_Z_VALUES': True,
            'OUTPUT': outputLayer
        }
        output = processing.run('native:dropmzvalues', parameters, context=context, feedback=feedback)

        return output['OUTPUT']

    @staticmethod
    def runDissolvePolygons(layer, context=None, feedback=None, outputLayer=None):
        outputLayer = 'memory:' if outputLayer is None else outputLayer
        parameters = {
            'INPUT': layer,
            'FIELD': [],
            'OUTPUT': outputLayer
        }
        output = processing.run('native:dissolve', parameters, context=context, feedback=feedback)

        return output['OUTPUT']

    def runYieldMapFiltering(self, parameters, context=None, feedback=None):

        outputDict = processing.run('r:Yield_map_filtering', parameters, context=context, feedback=feedback)
        return self._getLayerFromContext(outputDict, context)

    def runAddRasterValuesToPoints(self, shape, grid, context=None, feedback=None):

        parameters = {
            'SHAPES': shape,
            'GRIDS': grid,
            'RESAMPLING': 0,
            'RESULT': 'TEMPORARY_OUTPUT'
        }
        output = processing.run("saga:addrastervaluestopoints", parameters, context=context, feedback=feedback)
        return self._getLayerFromContext(output, context, field='RESULT')

    @staticmethod
    def runBasicStatisticsForFields(layer, field, context=None, feedback=None):

        parameters = {
            'INPUT_LAYER': layer,
            'FIELD_NAME': field,
            'OUTPUT_HTML_FILE': 'TEMPORARY_OUTPUT'
        }
        output = processing.run("qgis:basicstatisticsforfields", parameters, context=context, feedback=feedback)

        return output

    def runRasterCalculator(self, parameters, context=None, feedback=None):
        output = processing.run("qgis:rastercalculator", parameters, context=context, feedback=feedback)
        return self._getLayerFromContext(output, context, field='OUTPUT')

    def runPixelsToPoints(self, parameters, context=None, feedback=None):
        output = processing.run("native:pixelstopoints", parameters, context=context, feedback=feedback)
        return self._getLayerFromContext(output, context, field='OUTPUT')

    @staticmethod
    def runRMSE(layer, yieldField, errorField, context=None, feedback=None):
        parameters = {
            'VALIDATION_LAYER': layer,
            'YIELD_FIELD': yieldField,
            'ERROR_FIELD': errorField
        }
        return processing.run("lpc:rmse", parameters, context=context, feedback=feedback)

    # @staticmethod
    # def runErrorCompensation(t1Raster, t1ErrorRaster, t2Raster, t2ErrorRaster, exportPoints, context=None, feedback=None):
    #     parameters = {
    #         'T1_80_RASTER': t1Raster,
    #         'T1_ERROR_RASTER': t1ErrorRaster,
    #         'T2_80_RASTER': t2Raster,
    #         'T2_ERROR_RASTER': t2ErrorRaster,
    #         'POINTS': exportPoints
    #     }
    #     return processing.run("lpc:calculateerrorcompensation", parameters, context=context, feedback=feedback)

    @staticmethod
    def runFilterTreatments(layer, yieldField, t1output, t2output, context=None, feedback=None):

        parameters = {
            'YIELD_FILTERED_LAYER': layer,
            'TREATMENT_FIELD': yieldField,
            'TREATMENT_NAMES': [0, 1],
            'T1_OUTPUT': t1output,
            'T2_OUTPUT': t2output
        }
        return processing.run("lpc:filtertreatments", parameters, context=context, feedback=feedback)

    @staticmethod
    def runSimpleSample(layer, context=None, feedback=None):
        parameters = {
            'TREATMENT_FILTERED_LAYER': layer,
            'SAMPLE_VALUE': 80,
            'COMPLEMENTARY_VALUE': 20,
            'SAMPLE_OUTPUT': 'TEMPORARY_OUTPUT',
            'COMPLEMENTARY_OUTPUT': 'TEMPORARY_OUTPUT'
        }
        return processing.run("lpc:simplerandomsampling", parameters, context=context, feedback=feedback)

    @staticmethod
    def runHistogramFromAttribute(layer, field, path, context=None, feedback=None):
        parameters = {
            'YIELD_FILTERED_LAYER': layer,
            'YIELD_FIELD': field,
            'OUTPUT': path
        }
        return processing.run("lpc:histogramfromattribute", parameters, context=context, feedback=feedback)

    def runLoadComposerTemplates(self, project):
        layers = project.instance().mapLayers().values()
        contour = self.layerService.filterByLayerName(list(layers), ['_contour_'], inverse=True)
        parameters = {
            'INPUT_LAYERS': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'TRIAL_BOUNDS_LAYER': contour[0]
        }
        dialog = createAlgorithmDialog('lpc:loadcomposertemplates', parameters)
        dialog.show()
        dialog.exec_()

    @staticmethod
    def runExportMaps(project):
        parameters = {
            'LAYOUTS': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'RESOLUTION': 150,
            'OUTPUT': os.path.normpath(os.path.join(project.homePath(), '05_Results', '03_Maps'))
        }
        dialog = createAlgorithmDialog('lpc:exportmaps', parameters)
        dialog.show()
        dialog.exec_()

    @staticmethod
    def runCreateReport(parameters):

        dialog = createAlgorithmDialog('lpc:createreport', parameters)
        dialog.show()
        dialog.exec_()

    @staticmethod
    def runCreatePresentation(parameters):

        dialog = createAlgorithmDialog('lpc:createpresentation', parameters)
        dialog.show()
        dialog.exec_()

    @staticmethod
    def runCreateSampleLayers(parameters=None):
        if not parameters:
            parameters = {
                'YIELD_FILTERED_LAYER': 'T1_T2_total',
                'TREATMENT_FIELD': 'Traitement',
                'YIELD_FIELD': 'Prod_ha_h_',
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }

        dialog = createAlgorithmDialog('lpc:createsamplelayers', parameters)
        dialog.show()
        dialog.exec_()

    @staticmethod
    def runTreatmentPolygons(epsg, parameters=None):

        parameters['CRS'] = QgsCoordinateReferenceSystem(epsg)

        dialog = createAlgorithmDialog('lpc:treatmentpolygonsbuilder', parameters)
        dialog.show()
        dialog.exec_()

    @staticmethod
    def runHarvesterFilter(parameters=None):

        dialog = createAlgorithmDialog('lpc:filteringharvesterpoints', parameters)
        dialog.show()
        dialog.exec_()

    @staticmethod
    def runGainSurface(parameters):
        dialog = createAlgorithmDialog('lpc:creategainsurface', parameters)
        dialog.show()
        dialog.exec_()

    @staticmethod
    def runCalculateError(parameters):
        dialog = createAlgorithmDialog('lpc:calculateerror', parameters)
        dialog.show()
        dialog.exec_()

    @staticmethod
    def runErrorCompensation(parameters):
        dialog = createAlgorithmDialog('lpc:calculateerrorcompensation', parameters)
        dialog.show()
        dialog.exec_()
