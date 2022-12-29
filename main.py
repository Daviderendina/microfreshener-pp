import os.path

import click
from microfreshener.core.analyser import MicroToscaAnalyserBuilder
from microfreshener.core.analyser.costants import REFACTORING_NAMES, REFACTORING_ADD_API_GATEWAY, \
    REFACTORING_ADD_CIRCUIT_BREAKER, REFACTORING_ADD_MESSAGE_ROUTER, REFACTORING_USE_TIMEOUT, \
    REFACTORING_SPLIT_SERVICES, SMELLS_NAME
from microfreshener.core.importer import YMLImporter

from project.constants import IGNORE_CONFIG_SCHEMA_FILE
from project.exporter.yamlkexporter import YamlKExporter
from project.extender.extender import KubeExtender
from project.ignorer.impl.ignore_config import IgnoreConfig, IgnoreType
from project.ignorer.impl.ignore_nothing import IgnoreNothing
from project.importer.yamlkimporter import YamlKImporter
from project.report.report import RefactoringReport

from project.solver.solver import Solver, KubeSolver


SELECT_ALL = "all"

REFACTORING = ["add_api_gateway", "add_ag", "add_circuit_breaker", "add_cb", "add_message_router", "add_mr",
               "use_timeouts", "use_ts", "split_services", "split_svcs", SELECT_ALL]


@click.command()
@click.option("--kubedeploy", "--deploy", required=True, type=str, help="Folder containing Kubernetes deploy files of the system")
@click.option("--microtoscamodel", "--model", required=True, type=str, help="MicroTosca file containing the description of the system")
@click.option("--output", "--out", default="./out", type=str, help="Output folder of the tool")
@click.option("--impl", "-r", default=["all"], type=click.Choice(REFACTORING), help="Select and apply one impl. This option can be used multiple times, for adding more than one impl", multiple=True)
@click.option("--ignore_config", "--ig", type=str, help="The file that specifies which smell, refactoring or worker ignore")
def main(kubedeploy, microtoscamodel, output, refactoring: list, ignore_config):
    run(kubedeploy, microtoscamodel, output, refactoring, ignore_config)


def run(kubedeploy, microtoscamodel, output, refactoring: list, ignore_config_path):

    if not os.path.exists(kubedeploy):
        raise ValueError(f"Kubedeploy path passed as parameter ({kubedeploy}) not found")

    if not os.path.exists(microtoscamodel):
        raise ValueError(f"File passed as MicroTosca model ({microtoscamodel}) not found")

    if not os.path.exists(microtoscamodel):
        raise ValueError(f"File passed as ignore config ({ignore_config_path}) not found")

    if not os.path.exists(output):
        os.makedirs(output, 0o777)
        click.echo("Created output folder at: "+output)

    # Import model
    model = YMLImporter().Import(microtoscamodel)

    # Import Kubernetes Cluster
    importer = YamlKImporter()
    cluster = importer.Import(kubedeploy)

    # Read ignore config from disk
    ignore_config = IgnoreConfig(ignore_config_path, IGNORE_CONFIG_SCHEMA_FILE) if ignore_config_path else IgnoreNothing()

    # Run extender
    extender = KubeExtender()
    extender.set_all_workers()
    extender.extend(model, cluster)

    smell_solved = -1
    while smell_solved != 0:
        # Run sniffer on the model
        analyser = build_analyser(model, ignore_config)
        analyser_result = analyser.run(smell_as_dict=False)
        smells = [smell for sublist in [smell.get("smells", []) for sublist in analyser_result.values() for smell in sublist] for smell in sublist]

        # Run smell solver
        solver = build_solver(cluster, model, refactoring)
        smell_solved = solver.solve(smells)

        # Export files
        exporter = YamlKExporter()
        exporter.export(cluster, model, tosca_model_filename=microtoscamodel)

    # Export report
    RefactoringReport().export()


def build_analyser(model, ignore_config):
    analyser = MicroToscaAnalyserBuilder(model).add_all_sniffers().build()

    for node in model.nodes:
        for smell in SMELLS_NAME:
            if ignore_config.is_ignored(node, IgnoreType.SMELLS, smell):
                analyser.ignore_smell_for_node(node, smell)

    return analyser


def build_solver(cluster, model, refactoring) -> Solver:
    if SELECT_ALL in refactoring:
        return KubeSolver(cluster, model, REFACTORING_NAMES)

    selected_refactoring = []
    for r in refactoring:
        if r in ["add_api_gateway", "add_ag"]:
            selected_refactoring.append(REFACTORING_ADD_API_GATEWAY)

        if r in ["add_circuit_breaker", "add_cb"]:
            selected_refactoring.append(REFACTORING_ADD_CIRCUIT_BREAKER)

        if r in ["add_messagerouter", "add_mr"]:
            selected_refactoring.append(REFACTORING_ADD_MESSAGE_ROUTER)

        if r in ["use_timeouts", "use_ts"]:
            selected_refactoring.append(REFACTORING_USE_TIMEOUT)

        if r in ["split_services", "split_svcs"]:
            selected_refactoring.append(REFACTORING_SPLIT_SERVICES)


if __name__ == '__main__':
    run(
        microtoscamodel='./tests/data/robot-shop-v2/microTOSCA.yml',
        kubedeploy='./tests/data/robot-shop-v2/deployment',
        output="./out",
        refactoring=["all"],
        ignore_config_path=None
    )
