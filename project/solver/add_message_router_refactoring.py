from microfreshener.core.analyser.smell import Smell, EndpointBasedServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service

from k8s_template.kobject_generators import generate_ports_for_container, generate_svc_clusterIP_for_container
from project.exporter.export_object import ExportObject
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_container import KubeContainer
from project.solver.refactoring import Refactoring, RefactoringNotSupportedError
from project.utils.utils import check_ports_match


class AddMessageRouterRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model)

    def apply(self, smell: Smell):

        if not isinstance(smell, EndpointBasedServiceInteractionSmell):
            raise RefactoringNotSupportedError

        if isinstance(smell.node, Service):
            smell_container: KubeContainer = self.cluster.get_object_by_name(smell.node.name)

            if smell_container is None:
                return False

            container_workload_fullname: str = smell.node.name[len(smell_container.name) + 1:]
            container_workload_object = self.cluster.get_object_by_name(container_workload_fullname)

            if container_workload_object is not None:
                exposing_service = self.cluster.find_svc_exposing_workload(container_workload_object)

                if len(exposing_service) > 0:
                    port_compatible_services = [s for s in exposing_service if check_ports_match(s, smell_container)]

                    if len(port_compatible_services) > 0:
                        port_compatible_services.sort(key=lambda svc: len(self.cluster.find_workload_exposed_by_svc(svc)))

                        container_ports = generate_ports_for_container(
                            container=smell_container,
                            defining_obj=container_workload_object)
                        port_compatible_services[0].data["spec"]["ports"] += container_ports

                        return True
                    else:
                        #TODO se arrivo qui le porte non sono compatibili, ma devo capire una cosa: la porta che già espone
                        # è di quel pod oppure di altro? Questo va fatto nell'extender
                        generated_service = generate_svc_clusterIP_for_container(container=smell_container, defining_obj=container_workload_object)
                        self.cluster.add_object(generated_service)
                        self.cluster.add_export_object(ExportObject(generated_service, None))

                        return True
                else:
                    generated_service = generate_svc_clusterIP_for_container(container=smell_container, defining_obj=container_workload_object)
                    self.cluster.add_object(generated_service)
                    self.cluster.add_export_object(ExportObject(generated_service, None))

                    return True

            # Lo sviluppatore deve in qualche modo confermare di aver cambiato le chiamate, dall'IP al nome del svc
            # (il nome lo prendo direttamente dal pod/deploy/etc..) TODO Report refactoring

        return False

