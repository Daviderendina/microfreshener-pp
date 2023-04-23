from microfreshener.core.logging import MyLogger

from microkure.kmodel.kube_object_factory import KubeObjectFactory
from .kimporter import KImporter
from ..exporter.export_object import ExportObject
from ..kmodel.kube_cluster import KubeCluster
from ..utils.utils import get_filenames_from_directory, is_yaml, read_data_from_file


class YamlKImporter(KImporter):

    def __init__(self):
        super().__init__()
        self.cluster = KubeCluster()

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

