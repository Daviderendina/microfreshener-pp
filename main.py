import os.path

import click
from microfreshener.core.analyser import MicroToscaAnalyserBuilder
from microfreshener.core.analyser.costants import REFACTORING_NAMES, REFACTORING_ADD_API_GATEWAY, \
    REFACTORING_ADD_CIRCUIT_BREAKER, REFACTORING_ADD_MESSAGE_ROUTER, REFACTORING_USE_TIMEOUT, REFACTORING_SPLIT_SERVICES
from microfreshener.core.importer import YMLImporter

from project.extender.extender import KubeExtender
from project.importer.yamlkimporter import YamlKImporter

from project.solver.solver import Solver, KubeSolver

#TODO
'''
Tra i vari controlli effettuati ad es. per Gateway etc., manca quello sulle wildcard
'''

#TODO controllo che ci sia l'edge group

SELECT_ALL = "all"

REFACTORING = ["add_api_gateway", "add_ag", "add_circuit_breaker", "add_cb", "add_messagerouter", "add_mr",
               "use_timeouts", "use_ts", "split_services", "split_svcs", SELECT_ALL]



@click.command()
@click.option("--kubedeploy", "--deploy", required=True, type=str, help="Folder containing Kubernetes deploy files of the system")
@click.option("--microtoscamodel", "--model", required=True, type=str, help="MicroTosca file containing the description of the system")
@click.option("--output", "--out", default="./output", type=str, help="Output folder of the tool")
@click.option("--refactoring", "-r", default=["all"], type=click.Choice(REFACTORING), help="Select and apply one refactoring. This option can be used multiple times, for adding more than one refactoring", multiple=True)
def main(kubedeploy, microtoscamodel, output, apply_refactoring: list):

    if not os.path.exists(kubedeploy):
        raise ValueError(f"Kubedeploy path passed as parameter ({kubedeploy}) not found")

    if not os.path.exists(microtoscamodel):
        raise ValueError(f"File passed as MicroTosca model ({microtoscamodel}) not found")

    if not os.path.exists(output):
        os.makedirs(output, 0o777)
        click.echo("Created output folder at: "+output)

    # Import model
    model = YMLImporter().Import(microtoscamodel)

    # Import Kubernetes Cluster
    importer = YamlKImporter()
    cluster = importer.Import(kubedeploy)

    # Run extender
    extender = KubeExtender()
    extender.set_all_workers()
    extender.extend(model, cluster)

    # Run sniffer on the model
    analyser = MicroToscaAnalyserBuilder(model).add_all_sniffers().build()
    analyser_result = analyser.run()

    smells=[]
    for k, v in analyser_result.items():
        smells += v

    # Run smell solver
    solver = build_solver(cluster, apply_refactoring)
    solver.solve(smells)


def build_solver(cluster, refactoring) -> Solver:
    if SELECT_ALL in refactoring:
        return KubeSolver(cluster, REFACTORING_NAMES)

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
    main()