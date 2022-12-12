import copy
import uuid

from k8s_template.kubernetes_templates import SERVICE_CLUSTERIP_TEMPLATE, SERVICE_NODEPORT_TEMPLATE, \
    ISTIO_VIRTUAL_SVC_TIMEOUT_TEMPLATE
from project.kmodel.kube_container import KubeContainer
from project.kmodel.kube_istio import KubeVirtualService
from project.kmodel.kube_networking import KubeService
from project.kmodel.kube_object import KubeObject
from project.kmodel.kube_workload import KubePod, KubeWorkload

MF_NAME_SUFFIX = "MF"
MF_VIRTUALSERVICE_TIMEOUT_NAME = "VSTIMEOUT"


def generate_ports_for_container(defining_obj: KubeObject, container: KubeContainer):
    container_ports = []
    for port in container.get_ports():
        default_port_name = f"{defining_obj.fullname}-port-{port['containerPort']}-MF"

        new_port = {
            'name': port.get("name", default_port_name),
            'port': port.get("containerPort"),
        }

        protocol = port.get("protocol", None)
        if protocol:
            new_port['protocol'] = protocol

        target_port = port.get("targetPort", None)
        if target_port:
            new_port['target_port'] = target_port

        container_ports.append(new_port)

    return container_ports


def generate_ports_for_container_nodeport(defining_obj: KubeObject, container: KubeContainer, is_host_network: bool):
    # Extract ports from container
    service_ports = []

    container_ports = container.get_ports() if is_host_network else [p for p in container.get_ports() if p.get("hostPort")]
    for port in container_ports:
        default_port_name = f"{container.name}.{defining_obj.fullname}-port-{port['containerPort']}-MF"

        new_port = {
            'name': port.get("name", default_port_name),
            'port': port.get("containerPort")
        }

        if is_host_network:
            new_port['node_port'] = port.get("containerPort")
        else:
            node_port = port.get("hostPort", None)
            if node_port:
                new_port['node_port'] = node_port

        protocol = port.get("protocol", None)
        if protocol:
            new_port['protocol'] = protocol

        target_port = port.get("targetPort", None)
        if target_port:
            new_port['target_port'] = target_port

        service_ports.append(new_port)

    return service_ports


def generate_svc_clusterIP_for_container(defining_obj: KubeWorkload, container: KubeContainer) -> KubeService:
    # Extract ports from container
    container_ports = generate_ports_for_container(defining_obj, container)

    # Generate label
    service_selector = generate_random_label(defining_obj.fullname)

    # Generate service
    service_dict = SERVICE_CLUSTERIP_TEMPLATE.copy()
    service_dict["metadata"]["name"] = f"{defining_obj.name}-{MF_NAME_SUFFIX}"
    service_dict["metadata"]["namespace"] = defining_obj.namespace
    service_dict["spec"]["ports"] = container_ports
    service_dict["spec"]["selector"] = service_selector
    service = KubeService(service_dict)

    # Set labels to exposed object
    if isinstance(defining_obj, KubePod):
        defining_obj.set_labels(service_selector)
    else:
        defining_obj.add_pod_labels(service_selector)

    return service


def generate_svc_NodePort_for_container(defining_obj: KubeWorkload, container: KubeContainer, is_host_network: bool) -> KubeService:
    # Generate ports
    service_ports = generate_ports_for_container_nodeport(defining_obj, container, is_host_network)

    # Generate label
    service_selector = generate_random_label(defining_obj.fullname)

    # Generate service
    service_dict = copy.deepcopy(SERVICE_NODEPORT_TEMPLATE)
    service_dict["metadata"]["name"] = f"{defining_obj.name}-{MF_NAME_SUFFIX}"
    service_dict["metadata"]["namespace"] = defining_obj.namespace
    service_dict["spec"]["ports"] = service_ports
    service_dict["spec"]["selector"] = service_selector
    service = KubeService(service_dict)

    # Set labels to exposed object
    if isinstance(defining_obj, KubePod):
        defining_obj.set_labels(service_selector)
    else:
        defining_obj.add_pod_labels(service_selector)

    return service


def generate_random_label(label_key: str):
    name_suffix = f"-svc-{MF_NAME_SUFFIX}"
    return {f"{label_key}{name_suffix}": uuid.uuid4().hex}


def generate_timeout_virtualsvc_for_svc(service: KubeService, timeout: float):
    vservice_template = ISTIO_VIRTUAL_SVC_TIMEOUT_TEMPLATE.copy()
    vservice_template["metadata"]["name"] = f"{service.fullname}-{MF_VIRTUALSERVICE_TIMEOUT_NAME}-{MF_NAME_SUFFIX}"
    vservice_template["metadata"]["namespace"] = service.namespace
    vservice_template["spec"]["hosts"] = [service.fullname]
    vservice_template["spec"]["http"][0]["route"][0]["destination"]["host"] = service.fullname
    vservice_template["spec"]["http"][0]["timeout"] = f"{str(timeout)}s"

    return KubeVirtualService(vservice_template)
