from project.kmodel.kube_object import KubeObject


class KubeContainer(KubeObject):

    def __init__(self, data: dict):
        super().__init__(data)

    @property
    def name(self):
        return self.data.get("name", "")

    @property
    def ports(self):
        return self.data.get("ports", {})

    @property
    def fullname(self):
        return self.name

    def get_container_ports_numbers(self):
        result = [p.get("containerPort", None) for p in self.ports]
        return [p for p in result if p is not None]