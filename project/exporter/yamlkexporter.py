from datetime import datetime

from .export_object import ExportObject
from .exporter import Exporter
from ..constants import ImportExportConstants


class YamlKExporter(Exporter):

    def __init__(self, export_objects: list[ExportObject], output_folder=None):
        self.export_objects = export_objects
        if output_folder:
            self.output_folder = output_folder
        else:
            self.output_folder = ImportExportConstants.export_directory + "/" \
                                 + datetime.now().strftime("%Y%m%d_%H%M%S") + "/"

    def export(self):
        for export_obj in self.export_objects:
            export_obj.export(self.output_folder)

