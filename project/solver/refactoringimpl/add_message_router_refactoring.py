from microfreshener.core.analyser.smell import Smell, EndpointBasedServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import generate_ports_for_container, generate_svc_clusterIP_for_container
from project.exporter.export_object import ExportObject
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_container import KubeContainer
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring
from project.utils.utils import check_ports_match


class AddMessageRouterRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model)

    def _find_compatible_exposing_service(self, workload, container):
        selected_service = None

        exposing_service = self.cluster.find_svc_exposing_workload(workload)

        if len(exposing_service) > 0:
            port_compatible_services = [s for s in exposing_service if check_ports_match(s, container)]

            if len(port_compatible_services) > 0:
                port_compatible_services.sort(key=lambda svc: len(self.cluster.find_workload_exposed_by_svc(svc)))

                selected_service = port_compatible_services[0]

        return selected_service

    def apply(self, smell: Smell):

        if not isinstance(smell, EndpointBasedServiceInteractionSmell):
            raise RefactoringNotSupportedError

        if isinstance(smell.node, Service):
            smell_container: KubeContainer = self.cluster.get_object_by_name(smell.node.name)

            if smell_container is None:
                return False

            workload_fullname: str = smell.node.name[len(smell_container.name) + 1:]
            workload_object = self.cluster.get_object_by_name(workload_fullname)

            exposing_svc = self._find_compatible_exposing_service(workload_object, smell_container)

            if exposing_svc:
                container_ports = generate_ports_for_container(
                    container=smell_container,
                    defining_obj=workload_object)
                exposing_svc.data["spec"]["ports"] += container_ports

                self._refactor_model(smell.node, exposing_svc.fullname, smell.links_cause, svc_exists=True)

                return True

            else:
                #TODO se arrivo qui (se non trovo porte compatibili per il pod durante la ricerca) le porte non sono compatibili, ma devo capire una cosa: la porta che già espone
                # è di quel pod oppure di altro? Questo va fatto nell'extender - forse vedendo i file vecchi si capisce meglio cosa intendo
                generated_service = generate_svc_clusterIP_for_container(container=smell_container, defining_obj=workload_object)
                self.cluster.add_object(generated_service)
                self.cluster.add_export_object(ExportObject(generated_service, None))

                self._refactor_model(smell.node, generated_service.fullname, smell.links_cause, svc_exists=False)

                return True

        return False

        # Lo sviluppatore deve in qualche modo confermare di aver cambiato le chiamate, dall'IP al nome del svc
        # (il nome lo prendo direttamente dal pod/deploy/etc..) TODO Report refactoringimpl

    def _refactor_model(self, smell_node: Service, exposing_svc_name: str, smell_links, svc_exists: bool):
        message_router = self.model.get_node_by_name(exposing_svc_name, MessageRouter) \
            if svc_exists else MessageRouter(exposing_svc_name)

        if message_router:
            if not svc_exists:
                self.model.add_node(message_router)

            for interaction in smell_links:
                self.model.add_interaction(source_node=interaction.source, target_node=message_router)
                self.model.delete_relationship(interaction)

            # Search if relations between MR and Service also exists
            if len([r for r in message_router.interactions if r.target == smell_node and r.source == message_router]) == 0:
                self.model.add_interaction(source_node=message_router, target_node=smell_node)

            return True

        return False #TODO se ritorno false non succede nulla!! sistemare!!





