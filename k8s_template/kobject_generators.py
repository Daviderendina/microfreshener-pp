import uuid

from k8s_template.service_template import SERVICE_CLUSTERIP_TEMPLATE, SERVICE_NODEPORT_TEMPLATE
from project.kmodel.kContainer import KContainer
from project.kmodel.kObject import KObject
from project.kmodel.kPod import KPod
from project.kmodel.kService import KService


microfreshener_name_suffix = "MF"


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


def generate_svc_clusterIP_for_container(defining_obj: KObject, container: KContainer) -> KService:
    # Extract ports from container
    container_ports = generate_ports_for_container(defining_obj, container)

    # Generate label
    service_selector = generate_random_label(defining_obj.get_fullname())

    # Generate service
    service_dict = SERVICE_CLUSTERIP_TEMPLATE.copy()
    service_dict["metadata"]["name"] = f"{defining_obj.metadata.name}-{microfreshener_name_suffix}"
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
    # Extract ports from container
    service_ports = []
    for port in container.ports:
        default_port_name = f"{defining_obj.get_fullname()}-port-{port['containerPort']}-MF"

        new_port = {
            'name': port.get("name", default_port_name),
            'port': port.get("containerPort")
        }

        if is_host_network:
            new_port['node_port'] = port.get("containerPort")
        else:
            node_port = port.get("nodePort", None)
            if node_port:
                new_port['node_port'] = node_port

        protocol = port.get("protocol", None)
        if protocol:
            new_port['protocol'] = protocol

        target_port = port.get("targetPort", None)
        if target_port:
            new_port['target_port'] = target_port

        service_ports.append(new_port)

    # Generate label
    service_selector = generate_random_label(defining_obj.get_fullname())

    # Generate service
    service_dict = SERVICE_NODEPORT_TEMPLATE.copy()
    service_dict["metadata"]["name"] = f"{defining_obj.metadata.name}-{microfreshener_name_suffix}"
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
    name_suffix = f"-svc-{microfreshener_name_suffix}"
    return {f"{label_key}{name_suffix}": uuid.uuid4()}
