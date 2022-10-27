import yaml
from yaml.loader import SafeLoader
from microfreshener.core.logging import MyLogger

from project.kmodel.kCluster import KCluster, KObjectKind
from project.kmodel.kObject import KObject
from project.kObjectFactory import KObjectFactory
from .importer import Importer, get_filenames_from_directory


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


class YamlImporter(Importer):

    def __init__(self):
        super().__init__()
        self.cluster = KCluster()

    def Import(self, path: str) -> KCluster:
        filename_list = get_filenames_from_directory(path=path)
        MyLogger.get_logger().debug("Found {} files in folder {}: {}".format(
            len(filename_list), path, filename_list))

        for file in filename_list:
            if is_yaml(file):
                # Build objects
                data = read_data_from_file(path + "/" + file)
                for deploy_element in data:
                    kObject: KObject = KObjectFactory.build_object(object_dict=deploy_element, filename=file)

                    if kObject is None:
                        self.non_parsed.append((file, deploy_element))
                    else:
                        self.add_object_to_cluster(kObject)
            else:
                self.non_parsed.append((file, None))

        return self.cluster

    def add_object_to_cluster(self, object: KObject):
        kind: KObjectKind = KObjectKind.get_from_class(object.__class__)
        if kind is None:
            MyLogger.get_logger().debug(f"Cannot add object to cluster: {object.__class__} type not found "
                                    f"(KObjectKind.get_from_class)")
        else:
            self.cluster.add_object(object, kind)