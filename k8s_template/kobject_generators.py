import uuid

from k8s_template.kubernetes_templates import SERVICE_CLUSTERIP_TEMPLATE, SERVICE_NODEPORT_TEMPLATE, \
    ISTIO_VIRTUAL_SVC_TIMEOUT_TEMPLATE
from project.kmodel.istio import VirtualService
from project.kmodel.kContainer import KContainer
from project.kmodel.kObject import KObject
from project.kmodel.kPod import KPod
from project.kmodel.kService import KService


MF_NAME_SUFFIX = "MF"
MF_VIRTUALSERVICE_TIMEOUT_NAME = "VSTIMEOUT"


def generate_ports_for_container(defining_obj: KObject, container: KContainer):
    container_ports = []
    for port in container.ports:
        default_port_name = f"{defining_obj.get_fullname()}-port-{port['containerPort']}-MF"

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


def generate_ports_for_container_nodeport(defining_obj: KObject, container: KContainer, is_host_network: bool):
    # Extract ports from container
    service_ports = []

    container_ports = container.ports if is_host_network else [p for p in container.ports if p.get("hostPort")]
    for port in container_ports:
        default_port_name = f"{container.name}.{defining_obj.get_fullname()}-port-{port['containerPort']}-MF"

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


def generate_svc_clusterIP_for_container(defining_obj: KObject, container: KContainer) -> KService:
    # Extract ports from container
    container_ports = generate_ports_for_container(defining_obj, container)

    # Generate label
    service_selector = generate_random_label(defining_obj.get_fullname())

    # Generate service
    service_dict = SERVICE_CLUSTERIP_TEMPLATE.copy()
    service_dict["metadata"]["name"] = f"{defining_obj.metadata.name}-{MF_NAME_SUFFIX}"
    service_dict["metadata"]["namespace"] = defining_obj.get_namespace()
    service_dict["spec"]["ports"] = container_ports
    service_dict["spec"]["selector"] = service_selector
    service = KService.from_dict(service_dict)

    # Set labels to exposed object
    if isinstance(defining_obj, KPod):
        defining_obj.set_labels(service_selector)
    else:
        defining_obj.get_pod_template_spec().set_labels(service_selector)

    return service


def generate_svc_NodePort_for_container(defining_obj: KObject, container: KContainer, is_host_network: bool) -> KService:
    # Generate ports
    service_ports = generate_ports_for_container_nodeport(defining_obj, container, is_host_network)

    # Generate label
    service_selector = generate_random_label(defining_obj.get_fullname())

    # Generate service
    service_dict = SERVICE_NODEPORT_TEMPLATE.copy()
    service_dict["metadata"]["name"] = f"{defining_obj.metadata.name}-{MF_NAME_SUFFIX}"
    service_dict["metadata"]["namespace"] = defining_obj.get_namespace()
    service_dict["spec"]["ports"] = service_ports
    service_dict["spec"]["selector"] = service_selector
    service = KService.from_dict(service_dict)

    # Set labels to exposed object
    if isinstance(defining_obj, KPod):
        defining_obj.set_labels(service_selector)
    else:
        defining_obj.get_pod_template_spec().set_labels(service_selector)

    return service


def generate_random_label(label_key: str):
    name_suffix = f"-svc-{MF_NAME_SUFFIX}"
    return {f"{label_key}{name_suffix}": uuid.uuid4()}


def generate_timeout_virtualsvc_for_svc(service: KService, timeout: float):
    vservice_template = ISTIO_VIRTUAL_SVC_TIMEOUT_TEMPLATE.copy()
    vservice_template["metadata"]["name"] = f"{service.get_fullname()}-{MF_VIRTUALSERVICE_TIMEOUT_NAME}-{MF_NAME_SUFFIX}"
    vservice_template["metadata"]["namespace"] = service.get_namespace()
    vservice_template["spec"]["hosts"] = [service.get_fullname()]
    vservice_template["spec"]["http"][0]["route"][0]["destination"]["host"] = service.get_fullname()
    vservice_template["spec"]["http"][0]["timeout"] = f"{str(timeout)}s"

    return VirtualService.from_dict(vservice_template)
