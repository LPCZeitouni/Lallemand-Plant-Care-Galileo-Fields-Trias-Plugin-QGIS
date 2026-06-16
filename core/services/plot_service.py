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
import matplotlib.pyplot as plt
import matplotlib.patches as mPatches
import numpy as np

from qgis.PyQt.QtGui import QPalette, QColor
from ...gui.settings.options_settings_dlg import OptionsSettingsPage


class PlotterService:

    def __init__(self):
        self.settings = OptionsSettingsPage().getHistogramSettings()
        self.color = self.settings[1].getRgbF()
        self.edgeColor = self.settings[2].getRgbF()
        self.rowLabels = ['N of samples', 'Minimum', 'Maximum', 'Sum', 'Mean', 'Standard deviation',
                          'Coef variation (%)']
        self.rowTableLabels = [['N of samples'], ['Minimum'], ['Maximum'], ['Sum'], ['Mean'], ['Standard deviation'],
                               ['Coef variation (%)']]

    def createVFrequencyHistogram(self, values, tableData, title, exportPng=False, path=None):
        bins = int(self.settings[0])
        # Force un nombre raisonnable de bins (minimum 15-20 pour avoir une bonne résolution)
        bins = max(20, min(bins, 50))
        
        fontSize = 12
        cellText = np.hstack([self.rowTableLabels, tableData])
        fig = plt.figure(figsize=(4.2, 5))

        hist = fig.add_subplot(2, 1, 1)
        hist.hist(values, bins=bins, color=self.color, edgecolor=self.edgeColor)
        hist.set_title(f'{title} Histogram', fontsize=fontSize)
        hist.set_xlabel('Values', fontsize=fontSize)
        hist.set_ylabel('Frequency', fontsize=fontSize)

        ax2 = fig.add_subplot(2, 1, 2)
        bbox = [0, 0, 1, 0.6]
        ax2.axis('off')
        ax2.text(0.5, 0.605, 'Statistics', fontsize=12, ha='center', va='bottom')
        stats_table = ax2.table(cellText=cellText,
                                colWidths=[0.5, 0.6],
                                cellLoc='right', rowLoc='center',
                                bbox=bbox
                                )
        stats_table.auto_set_font_size(False)
        stats_table.set_fontsize(10)
        fig.tight_layout()

        outputPath = os.path.join(path, f'{title}_V.png')
        if exportPng:
            plt.savefig(outputPath, dpi=300, bbox_inches='tight')
        plt.close()

    def createFrequencyHistogram(self, values, tableData, title, exportPng=False, path=None):
        bins = int(self.settings[0])
        # Force un nombre raisonnable de bins (minimum 15-20 pour avoir une bonne résolution)
        bins = max(20, min(bins, 50))
        
        fontSize = 12
        cellText = np.hstack([self.rowTableLabels, tableData])
        fig = plt.figure(figsize=(6.5, 2.7))

        hist = fig.add_subplot(1, 2, 1)
        hist.hist(values, bins=bins, color=self.color, edgecolor=self.edgeColor)
        hist.set_title(f'{title} Histogram', fontsize=fontSize)
        hist.set_xlabel('Values', fontsize=fontSize)
        hist.set_ylabel('Frequency', fontsize=fontSize)

        ax2 = fig.add_subplot(1, 2, 2)
        bbox = [0, 0, 1, 0.6]
        ax2.axis('off')
        ax2.text(0.5, 0.605, 'Statistics', fontsize=12, ha='center', va='bottom')
        stats_table = ax2.table(cellText=cellText,
                                colWidths=[0.6, 0.5],
                                cellLoc='right', rowLoc='center',
                                bbox=bbox
                                )
        stats_table.auto_set_font_size(False)
        stats_table.set_fontsize(9)
        fig.tight_layout()

        outputPath = os.path.join(path, f'{title}_H.png')
        if exportPng:
            plt.savefig(outputPath, dpi=300, bbox_inches='tight')
        plt.close()

    def createStatisticsTable(self, tableData, title, exportPng=False, path=None):
        plt.figure()
        cellText = np.hstack([self.rowTableLabels, tableData])
        fig, ax = plt.subplots()

        statsTable = ax.table(cellText=cellText,
                              cellLoc='center', rowLoc='center',
                              loc='center', colWidths=[0.3, 0.3])
        plt.text(0.5, 0.67, f'{title} Statistics', fontsize=12, ha='center', va='bottom', transform=ax.transAxes)
        ax = plt.gca()
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.box(on=None)

        fig.tight_layout()
        outputPath = os.path.join(path, f'{title}_table.png')

        if exportPng:
            plt.savefig(outputPath, transparent=True, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def createGainStatisticsTable(pValue, statsData, anovaData, exportPng=False, path=None):
        fig = plt.figure(figsize=(5, 2.7))

        ax1 = fig.add_subplot(1, 2, 1)
        bbox = [0, 0, 0.8, 0.8]
        ax1.axis('off')
        ax1.text(-0.2, 0.82, 'Statistics', fontsize=12, ha='center', va='bottom')
        statsTable = ax1.table(cellText=statsData,
                               rowLabels=('Sum', 'Mean', 'Mode', 'Median', 'Standard Deviation'),
                               colWidths=[1, 0.6],
                               cellLoc='right', rowLoc='left',
                               bbox=bbox
                               )
        statsTable.auto_set_font_size(False)
        statsTable.set_fontsize(10)

        ax2 = fig.add_subplot(1, 2, 2)
        bbox = [0, 0, 1, 0.5]
        ax2.axis('off')
        ax2.text(0.25, 0.63, 'ANOVA Test', fontsize=12, ha='center', va='bottom')
        ax2.text(0.5, 0.515, f'P-Value = {pValue}', fontsize=10, ha='center', va='bottom')

        anovaTable = ax2.table(cellText=anovaData,
                               rowLabels=['Mean', 'Std. Dev.'],
                               colLabels=['T1', 'T2'],
                               colWidths=[0.5, 0.5],
                               cellLoc='center', rowLoc='center',
                               bbox=bbox
                               )
        anovaTable.auto_set_font_size(False)
        anovaTable.set_fontsize(10)

        fig.tight_layout()
        outputPath = os.path.join(path, f'Gain_Statistics_Table.png')

        if exportPng:
            plt.savefig(outputPath, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def yieldFrequencyHistogram(values, exportPng=False, path=None, thresholds=None, colors=None):
        """
        Histogramme des gains avec paliers et couleurs synchronisés avec la carte.
        """
        if not thresholds:
            thresholds = [0, 5, 15]
        if not colors:
            colors = ['#bfbcbc', '#ffff00', '#90EE90', '#006400'] # Gris, Jaune, Vert Clair, Vert Foncé
            
        total = len(values)
        data = np.array(values)

        plt.figure(figsize=(8, 5))
        # Utilisation de 50 bins pour une bonne précision visuelle
        n, bins, patches = plt.hist(values, bins=50, edgecolor='black', alpha=0.8)

        # Coloration dynamique de chaque barre de l'histogramme
        for i in range(len(patches)):
            center = (bins[i] + bins[i+1]) / 2
            if center < thresholds[0]:
                patches[i].set_facecolor(colors[0]) # Perte
            elif thresholds[0] <= center < thresholds[1]:
                patches[i].set_facecolor(colors[1]) # Faible
            elif thresholds[1] <= center < thresholds[2]:
                patches[i].set_facecolor(colors[2]) # Modéré
            else:
                patches[i].set_facecolor(colors[3]) # Fort

        # Calcul précis des pourcentages par classe pour la légende
        p_perte = (data[data < thresholds[0]].size / total) * 100
        p_faible = (data[(data >= thresholds[0]) & (data < thresholds[1])].size / total) * 100
        p_modere = (data[(data >= thresholds[1]) & (data < thresholds[2])].size / total) * 100
        p_fort = (data[data >= thresholds[2]].size / total) * 100

        # Création de la légende synchronisée
        labels = [
            f'Perte (<{thresholds[0]}%): {p_perte:.1f}%',
            f'Faible ({thresholds[0]}-{thresholds[1]}%): {p_faible:.1f}%',
            f'Modéré ({thresholds[1]}-{thresholds[2]}%): {p_modere:.1f}%',
            f'Fort (>{thresholds[2]}%): {p_fort:.1f}%'
        ]
        
        legend_patches = [mPatches.Patch(color=colors[i], label=labels[i]) for i in range(4)]
        plt.legend(handles=legend_patches, loc='upper right', title='Répartition des Gains', fontsize='small')

        plt.xlabel('Gain de rendement (%)')
        plt.ylabel('Fréquence (pixels)')
        plt.title('Distribution du Gain de Rendement')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        if exportPng:
            plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
