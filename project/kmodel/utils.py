from project.kmodel.kube_container import KubeContainer


def cast_container_list(container_list):
    return list(map(
        lambda c: KubeContainer(c),
        container_list
    ))
