import os

import yaml
from yaml import SafeLoader


def create_folder(path):
    file_folder = f"./{os.path.dirname(path)}"
    if not os.path.exists(file_folder):
        os.makedirs(file_folder, 0o777)


def get_filenames_from_directory(path: str) -> list:
    path = path if path.endswith("/") else f"{path}/"
    files = list()
    for folder, _, fnames in os.walk(path):
        for file in fnames:
            final_name = folder + "/" + file
            final_name = final_name.replace(path, "")
            final_name = final_name[1:] if final_name.startswith("/") else final_name
            files.append(final_name)
    return files


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