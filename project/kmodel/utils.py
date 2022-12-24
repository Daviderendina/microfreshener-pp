from project.kmodel.kube_container import KubeContainer


def cast_container_list(container_list, workload):
    return list(map(
        lambda c: KubeContainer(c, workload.fullname, workload.shortname),
        container_list
    ))
