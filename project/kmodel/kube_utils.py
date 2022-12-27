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


def name_has_namespace(name: str):
    match = re.match(r"([-\w]+)[.]([-\w]+)", name)
    return match and match.string == name
