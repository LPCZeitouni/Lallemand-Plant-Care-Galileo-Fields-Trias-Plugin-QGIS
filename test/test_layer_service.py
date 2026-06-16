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
import unittest
from unittest.mock import Mock
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsMessageBar
from core.services import LayerService
from core.services.message_service import MessageService


class TestLayerService(unittest.TestCase):

    def setUp(self):

        self.mock_iface = Mock()
        self.default_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        self.mock_project = QgsProject.instance()
        self.mock_message_bar = QgsMessageBar()
        self.mock_iface.messageBar.return_value = self.mock_message_bar
        self.mock_message_service = MessageService(self.mock_iface)
        self.layer_service = LayerService(self.mock_iface, self.default_crs)

    def tearDown(self):
        # Limpeza após cada teste, se necessário
        pass

    def test_create_vector_layer_valid(self):
        # Teste para o método create_vector_layer

        # Criar uma camada vetorial válida
        layer_name = "Test Layer"
        file_path = "path/to/valid_shapefile.shp"
        layer = self.layer_service.createVectorLayer(layer_name, file_path)

        # Verificar se a camada foi criada corretamente
        self.assertIsNotNone(layer)
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.name(), layer_name)

    # def test_create_layer_tree_group(self):
    #     # Teste para o método create_layer_tree_group
    #
    #     # Criar um projeto fictício para testes
    #     project = QgsProject.instance()
    #
    #     # Criar um grupo de camadas
    #     group_name = "Test Group"
    #     root = self.layer_service.create_layer_tree_group(project, group_name)
    #
    #     # Verificar se o grupo foi criado corretamente
    #     self.assertIsNotNone(root)
    #     self.assertIsInstance(root.findGroup(group_name), QgsLayerTreeGroup)
    #
    # def test_get_file_name(self):
    #     # Teste para o método get_file_name
    #
    #     # Caminho de arquivo de exemplo
    #     file_path = "path/to/example_file.shp"
    #
    #     # Obter o nome do arquivo sem extensão
    #     expected_file_name = "example_file"
    #     result_file_name = self.layer_service.get_file_name(file_path)
    #
    #     # Verificar se o nome do arquivo foi obtido corretamente
    #     self.assertEqual(result_file_name, expected_file_name)
    #
    # def test_convert_layer_crs(self):
    #     # Teste para o método convert_layer_crs
    #
    #     # Criar uma camada vetorial válida com CRS padrão
    #     layer_name = "Test Layer"
    #     file_path = "path/to/valid_shapefile.shp"
    #     source_layer = self.layer_service.create_vector_layer(layer_name, file_path)
    #
    #     # Definir um CRS de destino diferente
    #     target_crs = QgsCoordinateReferenceSystem("EPSG:3857")
    #
    #     # Realizar a conversão de CRS
    #     success = self.layer_service.convert_layer_crs(source_layer, target_crs)
    #
    #     # Verificar se a conversão foi bem-sucedida
    #     self.assertTrue(success)
    #     self.assertEqual(source_layer.crs().authid(), target_crs.authid())


if __name__ == '__main__':
    unittest.main()
