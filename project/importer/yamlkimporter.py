from typing import Tuple, List

import yaml
from yaml.loader import SafeLoader
from microfreshener.core.logging import MyLogger

from project.kmodel.kube_object_factory import KubeObjectFactory
from .kimporter import KImporter, get_filenames_from_directory
from ..exporter.export_object import ExportObject
from ..kmodel.kube_cluster import KubeCluster


def is_yaml(filename):
    return filename.lower().endswith(".yaml") or filename.lower().endswith(".yml")


def read_data_from_file(filename) -> list:
    read_data = list()
    with open(filename) as f:
        try:
            read_data = list(yaml.load_all(f, Loader=SafeLoader))
        except yaml.YAMLError as err:
            print("Exception while reading file: {} (error: {})".format(filename, err))
    return [i for i in read_data if i is not None]


class YamlKImporter(KImporter):

    def __init__(self):
        super().__init__()
        self.cluster = KubeCluster()
        self.export_objects: list[ExportObject] = []

    def Import(self, path: str) -> KubeCluster:
        filename_list = get_filenames_from_directory(path=path)
        MyLogger().get_logger().debug(f"Found {len(filename_list)} files in folder {path}: {filename_list}")

        for file in filename_list:
            file_fullpath = f"{path}/{file}"

            if is_yaml(file):

                # Build objects
                data = read_data_from_file(file_fullpath)
                for deploy_data in data:
                    kObject = KubeObjectFactory.build_object(object_dict=deploy_data, filename=file)

                    if kObject is not None:
                        self.cluster.add_object(kObject)
                        self.cluster.add_export_object(ExportObject(kObject, file))
                    else:
                        self.cluster.add_export_object(ExportObject(deploy_data, file))
            else:
                self.cluster.add_export_object(ExportObject(None, file))

        return self.cluster
