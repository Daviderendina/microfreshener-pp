import re

from project.kmodel.kube_container import KubeContainer
from project.kmodel.shortnames import ALL_SHORTNAMES


def cast_container_list(container_list, workload):
    return list(map(
        lambda c: KubeContainer(c, workload),
        container_list
    ))


def container_to_dict(container_list: list):
    return list(map(
        lambda c: c.data if isinstance(c, KubeContainer) else c,
        container_list
    ))


def does_selectors_labels_match(selectors: dict, labels: dict):
    selectors_str = [f"{k}:{v}" for k, v in selectors.items()]
    labels_str = [f"{k}:{v}" for k, v in labels.items()]

    return len([value for value in labels_str if value in selectors_str]) > 0


def does_svc_match_ports(service, ports):
    for svc_port in service.ports:
        for w_port in ports:
            target_port_match = \
                svc_port.get("targetPort", None) == w_port.get("name", "") or \
                svc_port.get("targetPort", None) == w_port.get("containerPort", "")
            protocol_match = svc_port.get("protocol", "TCP") == w_port.get("protocol", "TCP")

            if target_port_match and protocol_match:
                return True

    return False


def name_has_namespace(name: str):
    match = re.match(r"([-\w]+)[.]([-\w]+)", name)
    return match and match.string == name


def name_is_FQDN(name: str):
    regex = r"^[\w\-]+[.][\w\-]+[.](" + "|".join(ALL_SHORTNAMES) + ")[.]\w+[.]\w+"
    match = re.match(regex, name)
    return match and match.string == name
