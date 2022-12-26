from project.kmodel.kube_object import KubeObject


class KubeContainer(KubeObject):

    def __init__(self, data: dict, workload_fullname: str, workload_shortname: str):
        super().__init__(data)
        self.workload_fullname = workload_fullname
        self.workload_shortname = workload_shortname

    @property
    def name(self):
        return self.data.get("name", "")

    @property
    def ports(self):
        return self.data.get("ports", {})

    @property
    def fullname(self):
        return f"{self.name}.{self.workload_fullname}"

    @property
    def typed_fullname(self):
        return f"{self.name}.{self.workload_fullname}.{self.workload_shortname}"

    @property
    def defining_workload_fullname(self):
        return f"{self.workload_fullname}.{self.workload_shortname}"

    def get_container_ports_numbers(self):
        result = [p.get("containerPort", None) for p in self.ports]
        return [p for p in result if p is not None]
