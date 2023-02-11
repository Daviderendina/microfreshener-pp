from project.kmodel.kube_object import KubeObject


class KubeContainer(KubeObject):

    def __init__(self, data: dict, workload):
        super().__init__(data)
        self.defining_workload = workload

    @property
    def name(self):
        return self.data.get("name", "")

    @property
    def ports(self):
        return self.data.get("ports", {})

    @property
    def fullname(self):
        return f"{self.name}.{self.defining_workload.fullname}"

    @property
    def typed_fullname(self):
        return f"{self.name}.{self.defining_workload.typed_fullname}"

    @property
    def image(self):
        return self.data.get("image", "")

    def get_container_ports(self):
        result = []
        for p in self.ports:
            result.append(p.get("containerPort", None))
            result.append(p.get("name", None))

        return [p for p in result if p is not None]
