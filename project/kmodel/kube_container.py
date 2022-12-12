from project.kmodel.kube_object import KubeObject


class KubeContainer(KubeObject):

    def __init__(self, data: dict):
        super().__init__(data)

    @property
    def name(self):
        return self.data.get("name", "")

    def get_ports(self):
        return self.data.get("ports", {})

    def get_container_ports_numbers(self):
        result = [p.get("containerPort", None) for p in self.get_ports()]
        return [p for p in result if p is not None]

    @property
    def fullname(self):
        return self.name