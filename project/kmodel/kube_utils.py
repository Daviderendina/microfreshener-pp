import re

from project.kmodel.kube_container import KubeContainer


def cast_container_list(container_list, workload):
    return list(map(
        lambda c: KubeContainer(c, workload.fullname, workload.shortname),
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
