from typing import List, Dict

from project.kmodel.kube_object import KubeObject


class KubeIstio(KubeObject):
    pass


class KubeVirtualService(KubeIstio):

    def __init__(self, data: dict):
        super().__init__(data)

    def get_timeouts(self):
        result: List[(str, str, str)] = []

        for host in self.data.get('spec', {}).get('hosts', []):
            for http_route in self.data.get('spec', {}).get('http', []):
                for route in http_route.get("route", []):
                    timeout = http_route.get('timeout', None)
                    if timeout is not None:
                        destination = route.get('destination', {}).get('host', None)
                        if destination is not None:
                            result.append((host, destination, timeout))
        return result

    def get_destinations(self):
        result: List[str] = []
        for http_route in self.data.get('spec', {}).get('http', []):
            for destination_route in http_route.get('route', []):
                destination = destination_route.get('destination', {}).get('host', None)
                if destination is not None:
                    result.append(destination)
        return result

    def get_destinations_with_namespace(self):
        d = self.get_destinations()
        return list(map(lambda x: x + "." + self.namespace, d))

    def get_gateways(self):
        return self.data.get("spec", {}).get("gateways", [])

    def get_hosts(self):
        return self.data.get("spec", {}).get("hosts", [])

    def get_selectors(self) -> Dict[str, str]:
        return self.data.get("spec", {}).get("selector", None)


class KubeDestinationRule(KubeIstio):

    def __init__(self, data: dict):
        super().__init__(data)

    def is_circuit_breaker(self) -> bool:
        return self.data.get("spec", {}).get("trafficPolicy", {}).get("connectionPool", None) is not None \
            # and self.data.get("spec", {}).get("trafficPolicy", {}).get("outlierDetection", None) is not None

    def get_host(self):
        return self.data.get("spec", {}).get("host", None)

    def get_timeout(self) -> str:
        return self.data.get("spec", {}).get("trafficPolicy", {}).get("connectionPool", {})\
            .get("tcp", {}).get("connectionTimeout", None)


class KubeIstioGateway(KubeIstio):
    def __init__(self, data: dict):
        super().__init__(data)

    def get_all_host_exposed(self):
        result = []
        servers = self.data.get("spec", {}).get("servers", [])
        for server in servers:
            result += server.get("hosts", [])
        return result

    def get_selectors(self) -> list:
        return self.data.get("spec", {}).get("selector", [])