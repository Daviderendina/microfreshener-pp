from project.kmodel.kService import KService

# Template to which add metadata.name, metadata.labels, spec.ports, spec.selector
SERVICE_CLUSTERIP_TEMPLATE = {
    'api_version': 'v1',
    'kind': 'Service',
    'metadata': {
        # 'name': TODO,
        # 'namespace' : TODO
    },
    'spec': {
        'ports': [
            #{
            #    'name': TODO,
            #    'port': TODO,
            #}
        ],
        'selector': {
            #'label': 'value' TODO
        }
    }
}


def generate_service_from_template(name: str, namespace: str, ports: list, selector_labels: dict):
    service_dict = SERVICE_CLUSTERIP_TEMPLATE.copy()
    service_dict["metadata"]["name"] = name
    service_dict["metadata"]["namespace"] = namespace
    service_dict["spec"]["ports"] = ports
    service_dict["spec"]["selector"] = selector_labels

    return KService.from_dict(service_dict)


def generate_port_from_template(name: str, port: int, protocol: str = None, target_port: int = None) -> dict:
    port = {
        'name': name,
        'port': port,
    }

    if protocol:
        port['protocol'] = protocol

    if target_port:
        port['target_port'] = target_port

    return port