import os.path
from datetime import datetime

from microfreshener.core.exporter import YMLExporter
from microfreshener.core.model import MicroToscaModel

from .exporter import Exporter
from ..constants import ImportExportConstants
from ..context_vars import run_identifier, output_folder
from ..kmodel.kube_cluster import KubeCluster
from ..utils.utils import create_folder


class YamlKExporter(Exporter):

    KUBE_DEPLOY_FOLDER = "/kubernetes_deploy/"
    MICRO_TOSCA_MODEL = "/micro_tosca_model/"

    @property
    def kube_folder(self):
        return f"{output_folder}{self.KUBE_DEPLOY_FOLDER}"

    @property
    def tosca_file_path(self):
        return f"{output_folder}{self.MICRO_TOSCA_MODEL}"

    def export(self, cluster: KubeCluster, model: MicroToscaModel, tosca_model_filename=None):
        # Export cluster
        for export_obj in cluster.cluster_export_info:
            export_obj.export(f"{output_folder}{self.KUBE_DEPLOY_FOLDER}")

        # Export micro tosca model
        tosca_model_str = YMLExporter().Export(model)

        filename = os.path.basename(tosca_model_filename) if tosca_model_filename else model.name+".yml"
        tosca_output_filename = f"{output_folder}{self.MICRO_TOSCA_MODEL}{filename}"

        create_folder(tosca_output_filename)
        with open(tosca_output_filename, "w") as f:
            f.write(tosca_model_str)

