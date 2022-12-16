from project.kmodel.kube_container import KubeContainer


def cast_container_list(container_list, workload_fullname: str):
    return list(map(
        lambda c: KubeContainer(c, workload_fullname),
        container_list
    ))
