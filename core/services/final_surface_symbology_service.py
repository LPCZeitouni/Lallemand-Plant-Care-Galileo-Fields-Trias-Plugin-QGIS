# -*- coding: utf-8 -*-
"""
FinalSurfaceSymbologyService

Dedicated service for harmonising the symbology of T1_Final_Surface and
T2_Final_Surface before exporting maps and generating reports.

This service is intentionally isolated from LayerService in order to avoid
side effects on existing yield maps, gain maps, histograms or other plugin
workflows.
"""

from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsRasterBandStats,
    QgsColorRampShader,
    QgsRasterShader,
    QgsColorRampLegendNodeSettings,
    QgsSingleBandPseudoColorRenderer
)

from .message_service import MessageService
from ...gui.settings.options_settings_dlg import OptionsSettingsPage


class FinalSurfaceSymbologyService:
    """
    Harmonise the symbology of T1_Final_Surface and T2_Final_Surface.

    Business rule:
        - If T1 is the control, T1 defines the class limits and colours.
        - If T2 is the control, T2 defines the class limits and colours.
        - The same class limits and colours are then applied to both final surfaces.

    This makes T1_Final_Surface and T2_Final_Surface visually comparable
    in Word and PowerPoint reports.
    """

    PROJECT_CONTROL_VARIABLE = "galileo_control_treatment"

    T1_FINAL_SURFACE_NAMES = [
        "T1_Final_Surface",
        "T1 final surface",
        "T1_Final",
        "07_Model_T1"
    ]

    T2_FINAL_SURFACE_NAMES = [
        "T2_Final_Surface",
        "T2 final surface",
        "T2_Final",
        "08_Model_T2"
    ]

    def __init__(self):
        self.project = QgsProject.instance()
        self.messageService = MessageService()
        self.settings = OptionsSettingsPage()
        self.symbologySettings = self.settings.getSymbologySettings()

    def getControlTreatment(self):
        """
        Return the control treatment stored at project level.

        Expected values:
            T1
            T2
        """

        variables = QgsProject.instance().customVariables()
        control = variables.get(self.PROJECT_CONTROL_VARIABLE, None)

        if control in ["T1", "T2"]:
            return control

        return None

    def getControlScaleNote(self):
        """
        Return the report note explaining which treatment was used
        as reference for the common colour scale.
        """

        control = self.getControlTreatment()

        if control in ["T1", "T2"]:
            return f"Échelle fixée sur traitement contrôle : {control}"

        return "Échelle fixée sur traitement contrôle : non défini"

    def findLayerByCandidateNames(self, candidateNames):
        """
        Find a loaded QGIS layer using a list of possible names.

        The method first tries exact names. If not found, it then tries
        a contains-based search to remain tolerant to automatically
        generated layer names.
        """

        project = QgsProject.instance()

        for name in candidateNames:
            layers = project.mapLayersByName(name)
            if layers:
                return layers[0]

        allLayers = list(project.mapLayers().values())

        for candidate in candidateNames:
            for layer in allLayers:
                if candidate.lower() in layer.name().lower():
                    return layer

        return None

    def getFinalSurfaceLayers(self):
        """
        Return T1 and T2 final surface layers if available.
        """

        t1Layer = self.findLayerByCandidateNames(self.T1_FINAL_SURFACE_NAMES)
        t2Layer = self.findLayerByCandidateNames(self.T2_FINAL_SURFACE_NAMES)

        return t1Layer, t2Layer

    @staticmethod
    def calculateClasses(minValue, maxValue, numberClasses):
        """
        Calculate class boundaries from min to max.

        This mirrors the existing logic used in LayerService for raster
        symbology.
        """

        if numberClasses <= 1:
            return [round(minValue, 1), round(maxValue, 1)]

        step = (maxValue - minValue) / (numberClasses - 1)
        return [round(minValue + i * step, 1) for i in range(numberClasses)]

    @staticmethod
    def createRasterClassLabel(index, classInterval):
        """
        Create labels for raster legend classes.
        """

        if index == 0:
            return f"< {classInterval[index]}"

        if index == len(classInterval) - 1:
            return f"> {classInterval[index]}"

        return f"{classInterval[index]} - {classInterval[index + 1]}"

    def getNumberOfClasses(self):
        """
        Return the number of classes configured in plugin settings.
        """

        try:
            return int(self.symbologySettings[0])
        except Exception:
            return 4

    def getColors(self):
        """
        Return the colour list configured in plugin settings.

        The plugin settings may return either:
            [4, ['#color1', '#color2', ...]]
        or:
            [4, '#color1', '#color2', ...]
        This method supports both forms.
        """

        if len(self.symbologySettings) > 1 and isinstance(self.symbologySettings[1], list):
            return list(self.symbologySettings[1])

        if len(self.symbologySettings) > 1:
            return list(self.symbologySettings[1:])

        return ["#bfbcbc", "#ffff00", "#55ff00", "#267300"]

    def createColorRampItemList(self, classes, colors):
        """
        Create QgsColorRampShader items using fixed classes and colours.
        """

        colorItemList = []

        for index, value in enumerate(classes):
            color = colors[index] if index < len(colors) else colors[-1]
            label = self.createRasterClassLabel(index, classes)
            colorItemList.append(
                QgsColorRampShader.ColorRampItem(value, QColor(color), label)
            )

        return colorItemList

    @staticmethod
    def createRasterLegendSettings():
        """
        Create legend settings for class-based raster rendering.
        """

        legendSettings = QgsColorRampLegendNodeSettings()
        legendSettings.setUseContinuousLegend(False)
        return legendSettings

    @staticmethod
    def createRasterShader(colorRamp):
        """
        Create a raster shader from a colour ramp.
        """

        rasterShader = QgsRasterShader()
        rasterShader.setRasterShaderFunction(colorRamp)
        return rasterShader

    def createFixedRasterRenderer(self, rasterLayer, minValue, maxValue):
        """
        Create a raster renderer using fixed min/max values.

        The same fixed min/max values are applied to both T1 and T2 final
        surfaces, making the colour scale strictly comparable.
        """

        numberClasses = self.getNumberOfClasses()
        colors = self.getColors()

        classes = self.calculateClasses(minValue, maxValue, numberClasses)
        colorItems = self.createColorRampItemList(classes, colors)

        legendSettings = self.createRasterLegendSettings()

        colorRamp = QgsColorRampShader()
        colorRamp.setColorRampItemList(colorItems)
        colorRamp.setColorRampType(QgsColorRampShader.Interpolated)
        colorRamp.setLegendSettings(legendSettings)

        rasterShader = self.createRasterShader(colorRamp)

        renderer = QgsSingleBandPseudoColorRenderer(
            rasterLayer.dataProvider(),
            1,
            rasterShader
        )

        renderer.setClassificationMin(minValue)
        renderer.setClassificationMax(maxValue)

        return renderer

    @staticmethod
    def getRasterMinMax(rasterLayer):
        """
        Return min and max values from band 1 of a raster layer.
        """

        stats = rasterLayer.dataProvider().bandStatistics(
            1,
            QgsRasterBandStats.All
        )

        return stats.minimumValue, stats.maximumValue

    def applyRasterSymbology(self, t1Layer, t2Layer, control):
        """
        Apply common raster symbology to T1 and T2 final surfaces.
        """

        if control == "T1":
            referenceLayer = t1Layer
        else:
            referenceLayer = t2Layer

        minValue, maxValue = self.getRasterMinMax(referenceLayer)

        t1Renderer = self.createFixedRasterRenderer(t1Layer, minValue, maxValue)
        t2Renderer = self.createFixedRasterRenderer(t2Layer, minValue, maxValue)

        t1Layer.setRenderer(t1Renderer)
        t2Layer.setRenderer(t2Renderer)

        t1Layer.triggerRepaint()
        t2Layer.triggerRepaint()

    def applyVectorFallbackSymbology(self, t1Layer, t2Layer, control):
        """
        Fallback for non-raster layers.

        If final surfaces are vector layers instead of raster layers,
        this method clones the renderer of the control layer and applies
        it to the other layer.
        """

        if control == "T1":
            referenceLayer = t1Layer
            targetLayer = t2Layer
        else:
            referenceLayer = t2Layer
            targetLayer = t1Layer

        renderer = referenceLayer.renderer()

        if renderer is None:
            return

        targetLayer.setRenderer(renderer.clone())

        referenceLayer.triggerRepaint()
        targetLayer.triggerRepaint()

    def applyControlSymbologyToFinalSurfaces(self, control=None):
        """
        Main public method.

        Harmonise symbology between T1_Final_Surface and T2_Final_Surface.
        """

        if control is None:
            control = self.getControlTreatment()

        if control not in ["T1", "T2"]:
            self.messageService.logMessage(
                "Final surface symbology not applied: no valid control treatment defined.",
                1
            )
            return False

        t1Layer, t2Layer = self.getFinalSurfaceLayers()

        if t1Layer is None or t2Layer is None:
            self.messageService.logMessage(
                "Final surface symbology not applied: T1_Final_Surface or T2_Final_Surface not found.",
                1
            )
            return False

        try:
            if isinstance(t1Layer, QgsRasterLayer) and isinstance(t2Layer, QgsRasterLayer):
                self.applyRasterSymbology(t1Layer, t2Layer, control)
            else:
                self.applyVectorFallbackSymbology(t1Layer, t2Layer, control)

            self.messageService.logMessage(
                f"Final surface symbology applied using control treatment: {control}",
                3
            )

            return True

        except Exception as exception:
            self.messageService.logMessage(
                f"Error while applying final surface symbology: {str(exception)}",
                2
            )
            return False
