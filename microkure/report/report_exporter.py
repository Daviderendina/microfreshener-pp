from microfreshener.core.analyser.smell import NodeSmell, GroupSmell

from microkure.constants import REPORT_OUTPUT_FOLDER
from microkure.utils.utils import create_folder


class ReportExporter:

    report = ""
    filename = ""

    def __init__(self, filename):
        self.report = ""
        self.export_file = f"{REPORT_OUTPUT_FOLDER}/{filename}"

    @staticmethod
    def export(self, report):
        pass

    def _write_to_file(self):
        create_folder(self.export_file)
        with open(self.export_file, "w") as report_file:
            report_file.write(self.report)


class RefactoringCSVReportExporter(ReportExporter):

    filename = "refactoring_report.csv"
    header = "Refactoring;Smell;Status;Tosca Node;Caused by;Message;\n"

    def __init__(self):
        super(RefactoringCSVReportExporter, self).__init__(self.filename)

    def export(self, report):
        self.report += self.header

        for row in report.rows:
            node = self._get_node_csv(row.smell)
            cause_nodes = self._get_cause_nodes_csv(row.smell)
            message = f"\"" + '\n'.join(row.message_list) + "\""

            self.report += f"{row.refactoring_name};{row.smell.name};{row.status.name};{node};{cause_nodes};{message};\n"

        self._write_to_file()

    def _get_node_csv(self, smell):
        node = ""
        if isinstance(smell, NodeSmell):
            node = smell.node.name
        elif isinstance(smell, GroupSmell):
            node = smell.group.name
            node += " ("
            for n in smell.group.members:
                node += f"{n.name}, "
            node = node[:-2] + ")"

        return node

    def _get_cause_nodes_csv(self, smell):
        cause_nodes = ""
        if isinstance(smell, NodeSmell):
            cause_nodes = str([n.target.name for n in smell.links_cause])[1:-1]

        return cause_nodes
