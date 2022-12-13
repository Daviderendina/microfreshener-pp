from datetime import datetime

from .export_object import ExportObject
from .exporter import Exporter
from ..constants import ImportExportConstants
from ..kmodel.kube_cluster import KubeCluster


class YamlKExporter(Exporter):

    def __init__(self, output_folder=None):
        if output_folder:
            self.output_folder = output_folder
        else:
            self.output_folder = ImportExportConstants.export_directory + "/" \
                                 + datetime.now().strftime("%Y%m%d_%H%M%S") + "/"

    def export(self, cluster: KubeCluster):
        for export_obj in cluster.cluster_export_info:
            export_obj.export(self.output_folder)

