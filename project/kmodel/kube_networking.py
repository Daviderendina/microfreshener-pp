from project.kmodel.kube_object import KubeObject


class KubeNetworking(KubeObject):
    pass


class KubeService(KubeNetworking):

    def __init__(self, data: dict):
        super().__init__(data)

    @property
    def selectors(self):
        return self.data.get("spec", {}).get("selector", {})

    @property
    def ports(self):
        return self.data.get("spec", {}).get("ports", [])

    '''
    Return true if the service is accessible from outside the network
    '''
    def is_reachable_from_outside(self):
        return self.data.get("spec", {}).get("type", "ClusterIP") != "ClusterIP"


class KubeIngress(KubeNetworking):

    def __init__(self, data: dict):
        super().__init__(data)

    def get_exposed_svc_names(self):
        result = list()

        rules = self.data.get("spec", {}).get("rules", [])
        for rule in rules:
            paths = rule.get("http", {}).get("paths", [])
            for path in paths:
                svc_name = path.get("backend", {}).get("service", {}).get("name", None)
                if svc_name:
                    result.append(svc_name)

        return result
