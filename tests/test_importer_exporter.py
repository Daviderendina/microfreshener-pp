import os
import uuid
from unittest import TestCase

from project.exporter.yamlkexporter import YamlKExporter
from project.importer.yamlkimporter import YamlKImporter


class TestImporterExporter(TestCase):

    TEST_FILES_PATH = "./data/import_export_test_files"
    NEW_NAME_STR = f"NEW-{uuid.uuid4().hex}"

    def test_import_export(self):
        # Import files
        importer = YamlKImporter()
        cluster, export_objects = importer.Import(self.TEST_FILES_PATH)

        # Check that cluster has been created properly
        self.assertEqual(len(cluster.cluster_objects), 7)
        self.assertEqual(len(export_objects), 11)

        # Modify cluster elements
        for obj in cluster.cluster_objects:
            obj.data["metadata"]["name"] = self.NEW_NAME_STR + obj.data["metadata"].get("name", "DEFAULT_NAME")

        # Export files
        exporter = YamlKExporter(export_objects)
        exporter.export()

        # Read files in order to find modification
        check_importer = YamlKImporter()
        cluster, export_objects = check_importer.Import(exporter.output_folder)

        # Check that cluster had been exported properly
        self.assertEqual(len(cluster.cluster_objects), 7)
        self.assertEqual(len(export_objects), 11)

        # Check that exported objects are updated in name
        for obj in cluster.cluster_objects:
            self.assertTrue(obj.name.startswith(self.NEW_NAME_STR))

        # Check folder structure
        files=[]
        for folder, _, fnames in os.walk(self.TEST_FILES_PATH):
            for file in fnames:
                files.append(file)

        for folder, _, fnames in os.walk(exporter.output_folder):
            for file in fnames:
                files.remove(file)

        self.assertEqual(files, [])