from abc import ABC, abstractmethod

import os

from project.kmodel.kube_cluster import KubeCluster


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


class KImporter(ABC):

    def __init__(self):
        self.non_parsed = list()

    @abstractmethod
    def Import(self, path: str) -> KubeCluster:
        pass
