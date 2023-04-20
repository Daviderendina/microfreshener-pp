import os
import shutil

import yaml

from microfreshenerpp.constants import DEPLOY_OUTPUT_FOLDER, GENERATED_DEPLOY_OUTPUT_FOLDER
from microfreshenerpp.kmodel.kube_object import KubeObject
from microfreshenerpp.utils.utils import create_folder


class ExportObject:

    def __init__(self, kube_object, filename):
        self.kube_object = kube_object
        self.filename = filename
        self.out_fullname = self._get_output_fullname()

    def export(self):
        create_folder(self.out_fullname)

        if self.kube_object is None:
            shutil.copy(self.filename, self.out_fullname)
        elif isinstance(self.kube_object, dict) or isinstance(self.kube_object, KubeObject):
            self._write_to_file()

    def _get_output_fullname(self):
        if self.filename:
            return f"{DEPLOY_OUTPUT_FOLDER}/{self.filename}"
        else:
            return f"{GENERATED_DEPLOY_OUTPUT_FOLDER}/{self.kube_object.typed_fullname}.yaml"

    def _write_to_file(self):
        YAML_SEPARATOR = "\n---\n\n"

        content = self.kube_object.data if isinstance(self.kube_object, KubeObject) else self.kube_object

        if isinstance(content, dict):
            c = yaml.dump(content, sort_keys=False)

            file_exists = os.path.exists(self.out_fullname)
            with open(self.out_fullname, "a" if file_exists else "w") as f:
                if file_exists:
                    f.write(YAML_SEPARATOR)
                f.write(c)
