import os
import uuid
from unittest import TestCase

from microfreshener.core.importer import YMLImporter

from project.constants import OUTPUT_FOLDER, DEPLOY_OUTPUT_FOLDER, TOSCA_OUTPUT_FOLDER
from project.exporter.yamlkexporter import YamlKExporter
from project.importer.yamlkimporter import YamlKImporter


class TestImporterExporter(TestCase):

    TEST_FILES_PATH = "./data/import_export_test_files"
    TEST_FILES_PATH_KUBE = f"{TEST_FILES_PATH}/deploy"
    TEST_FILES_PATH_TOSCA = f"{TEST_FILES_PATH}/helloworld.yml"
    NEW_NAME_STR = f"NEW-{uuid.uuid4().hex}"

    def test_import_export(self):
        # Import files
        cluster = YamlKImporter().Import(self.TEST_FILES_PATH_KUBE)
        model = YMLImporter().Import(self.TEST_FILES_PATH_TOSCA)

        # Check that cluster has been created properly
        self.assertEqual(len(cluster.cluster_objects), 7)
        self.assertEqual(len(cluster.cluster_export_info), 11)

        # Modify cluster elements
        for obj in cluster.cluster_objects:
            obj.data["metadata"]["name"] = self.NEW_NAME_STR + obj.data["metadata"].get("name", "DEFAULT_NAME")

        # Export files
        exporter = YamlKExporter()
        exporter.export(cluster, model, tosca_model_filename=self.TEST_FILES_PATH_TOSCA)

        # Read files in order to find modification
        check_importer = YamlKImporter()
        cluster = check_importer.Import(DEPLOY_OUTPUT_FOLDER)#f"{exporter.output_folder}{exporter.KUBE_DEPLOY_FOLDER}")

        # Check that cluster had been exported properly
        self.assertEqual(len(cluster.cluster_objects), 7)
        self.assertEqual(len(cluster.cluster_export_info), 11)

        # Check that exported objects are updated in name
        for obj in cluster.cluster_objects:
            self.assertTrue(obj.name.startswith(self.NEW_NAME_STR))

        # Check folder structure
        dirs = os.listdir(OUTPUT_FOLDER)
        self.assertEqual(len(dirs), 2)
        self.assertTrue(DEPLOY_OUTPUT_FOLDER.replace(OUTPUT_FOLDER+"/", "") in dirs)
        self.assertTrue(TOSCA_OUTPUT_FOLDER.replace(OUTPUT_FOLDER+"/", "") in dirs)

        # Controllo che il file TOSCA sia al suo posto
        files = []
        for folder, _, fnames in os.walk(self.TEST_FILES_PATH_KUBE):
            for file in fnames:
                files.append(file)

        for folder, _, fnames in os.walk(DEPLOY_OUTPUT_FOLDER):
            for file in fnames:
                files.remove(file)

        self.assertEqual(files, [])


