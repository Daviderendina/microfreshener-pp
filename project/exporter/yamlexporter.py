import shutil
import yaml
import os
from datetime import datetime

from .exporter import Exporter
from ..constants import ImportExportConstants
from ..kmodel.kCluster import KCluster
from ..utils.utils import create_folder


def dict_to_yaml(dictionary: dict):
    return yaml.dump(dictionary, sort_keys=False)


def write_to_file_yml(filename: str, content):
    if isinstance(content, dict):
        c = dict_to_yaml(content)

    file_exists = os.path.exists(filename)
    with open(filename, "a" if file_exists else "w") as f:
        if file_exists:
            f.write(YamlExporter.YAML_SEPARATOR)
        f.write(c)


class YamlExporter(Exporter):
    YAML_SEPARATOR = "\n---\n\n"

    def __init__(self):
        self.default_output_folder = ImportExportConstants.export_directory + "/" \
                                     + datetime.now().strftime("%Y%m%d_%H%M%S") + "/"

    def export(self, cluster: KCluster):

        for kType in cluster.cluster_objects.keys():
            for kObject in cluster.cluster_objects.get(kType, []):
                output_filename = self._get_output_fullname(kObject.export_filename)
                create_folder(output_filename)
                write_to_file_yml(output_filename, kObject.to_dict_yaml())

    def export_non_parsed(self, non_parsed: list):
        for filename, content in non_parsed:
            new_filename = self._get_output_fullname(filename)
            create_folder(new_filename)

            if content is None:
                shutil.copyfile(ImportExportConstants.import_directory + "/" + filename, new_filename)
            else:
                write_to_file_yml(new_filename, content)

    def _get_output_fullname(self, file: str):
        return self.default_output_folder + file
