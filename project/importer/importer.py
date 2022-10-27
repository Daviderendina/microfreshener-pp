from abc import ABC, abstractmethod

import os

from project.kmodel.kCluster import KCluster


def get_filenames_from_directory(path) -> list:
    files = list()
    for folder, _, fnames in os.walk(path):
        for file in fnames:
            final_name = folder + "/" + file
            files.append(final_name.replace(path + "/", ""))
    return files


class Importer(ABC):

    def __init__(self):
        self.non_parsed: list[(str, str)] = list()

    @abstractmethod
    def Import(self, path: str) -> KCluster:
        pass
