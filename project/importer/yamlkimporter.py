import yaml
from yaml.loader import SafeLoader
from microfreshener.core.logging import MyLogger

from project.kmodel.kObjectFactory import KObjectFactory
from .kimporter import KImporter, get_filenames_from_directory
from project.kmodel.v2 import Cluster


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
        self.cluster = Cluster()

    def Import(self, path: str) -> Cluster:
        filename_list = get_filenames_from_directory(path=path)
        MyLogger().get_logger().debug(f"Found {len(filename_list)} files in folder {path}: {filename_list}")

        for file in filename_list:
            if is_yaml(file):
                # Build objects
                data = read_data_from_file(path + "/" + file)
                for deploy_element in data:
                    kObject = KObjectFactory.build_object(object_dict=deploy_element, filename=file)

                    if kObject is None:
                        self.non_parsed.append((file, deploy_element))
                    else:
                        self.cluster.add_object(object)
            else:
                self.non_parsed.append((file, None))

        return self.cluster
