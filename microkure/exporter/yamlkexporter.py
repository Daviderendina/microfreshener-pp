import os.path

from microfreshener.core.exporter import YMLExporter
from microfreshener.core.model import MicroToscaModel

from .exporter import Exporter
from ..constants import TOSCA_OUTPUT_FOLDER
from ..kmodel.kube_cluster import KubeCluster
from ..utils.utils import create_folder


class YamlKExporter(Exporter):

    def export(self, cluster: KubeCluster, model: MicroToscaModel, tosca_model_filename=None):
        # Export cluster
        for export_obj in cluster.cluster_export_info:
            export_obj.export()

        # Export micro tosca model
        tosca_model_str = YMLExporter().Export(model)

        filename = os.path.basename(tosca_model_filename) if tosca_model_filename else model.name+".yml"
        tosca_output_filename = f"{TOSCA_OUTPUT_FOLDER}/{filename}"

        create_folder(tosca_output_filename)
        with open(tosca_output_filename, "w") as f:
            f.write(tosca_model_str)

