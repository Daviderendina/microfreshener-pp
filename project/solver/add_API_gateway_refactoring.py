from typing import List

from microfreshener.core.analyser.smell import Smell, NoApiGatewaySmell
from microfreshener.core.model import MicroToscaModel, Service

from k8s_template.kobject_generators import generate_svc_NodePort_for_container, generate_ports_for_container_nodeport
from project.kmodel.kube_cluster import KubeCluster
from project.solver.refactoring import Refactoring, RefactoringNotSupportedError


class AddAPIGatewayRefactoring(Refactoring):
    # https://alesnosek.com/blog/2017/02/14/accessing-kubernetes-pods-from-outside-of-the-cluster/
    def __init__(self, model: MicroToscaModel, cluster: KubeCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):
        if not isinstance(smell, NoApiGatewaySmell):
            raise RefactoringNotSupportedError

        # Handle Message Broker case
            #TODO per me non si può fare

        if isinstance(smell.node, Service):
            container, def_object = self._get_container_and_def_object(smell.node.name)

            ports_to_expose = generate_ports_for_container_nodeport(
                def_object, container, def_object.is_host_network()
            )
            expose_svc = self._search_for_existing_svc(def_object, ports_to_expose)
            if expose_svc:
                svc_ports = expose_svc.get_ports()
                svc_ports += ports_to_expose

            else:
                node_port_service = generate_svc_NodePort_for_container(
                    defining_obj=def_object,
                    container=container,
                    is_host_network=def_object.is_host_network()
                )
                self.cluster.add_object(node_port_service)

            if def_object.is_host_network():
                # def_object.set_host_network(False) TODO qui c'è un problema: non posso toglierlo senza prima essere
                # sicuro che non ci siano altri smell sugli altri container definiti dal pod. Togliendolo fregandomene di
                # tutto rischio di fare un casino, perché poi non mi becca più lo smell

                # La soluzione più comoda mi sembra quella di creare una classe PendingOperations che viene chiamata dopo
                # tutta l'analisi e prima della scrittura del cluster su disco.
                pass

            else:
                for port in container.get_ports():
                    if port.get("hostPort"):
                        del port["hostPort"]

        return self.cluster

    def _get_container_and_def_object(self, service_node_name: str):
        container = self.cluster.get_object_by_name(service_node_name)
        def_object = None

        if container:
            def_object = self.cluster.find_workload_defining_container(service_node_name)

        return container, def_object

    def _search_for_existing_svc(self, defining_obj, ports_to_open: List[int]):
        port_numbers = [p.get('node_port', p.get('port')) for p in ports_to_open]
        services = [s for s in self.cluster.find_svc_exposing_workload(defining_obj)
                    if self._check_ports(s, port_numbers)]

        if len(services) == 0:
            return None
        elif len(services) == 1:
            expose_svc = services[0]
        else:
            services = sorted(services, key=self.cluster.find_svc_exposing_workload)
            expose_svc = services[0]

        return expose_svc

    def _check_ports(self, svc, ports_to_check: List[int]):
        for svcport in svc.get_ports():
            exposed_port = svcport.get('node_port', svcport.get('port', None))
            if exposed_port and exposed_port in ports_to_check:
                return False

        return True




