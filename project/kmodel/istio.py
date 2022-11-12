from project.kmodel.kObject import KObject


class VirtualService(KObject):

    def __init__(self, data: dict):
        self.data: dict = data

    @staticmethod
    def from_dict(dictionary):
        return VirtualService(data=dictionary)

    def get_timeouts(self) -> list[(str, str, str)]:
        result: list[(str, str, str)] = []
        for host in self.data.get('spec', {}).get('hosts', []):
            for http_route in self.data.get('spec', {}).get('http', []):
                timeout = http_route.get('timeout', None)
                if timeout is not None:
                    for destination_route in http_route.get('route', []):
                        destination = destination_route.get('destination', {}).get('host', None)
                        if destination is not None:

                            result.append((host, destination, timeout))
        return result

    def get_destinations(self) -> list[str]:
        result: list[str] = []
        for http_route in self.data.get('spec', {}).get('http', []):
            for destination_route in http_route.get('route', []):
                destination = destination_route.get('destination', {}).get('host', None)
                if destination is not None:
                    result.append(destination)
        return result

    def get_destinations_with_namespace(self) -> list[str]:
        d = self.get_destinations()
        return list(map(lambda x: x + "." + self.get_namespace(), d))

    def get_gateways(self) -> list[str]:
        return self.data.get("spec", {}).get("gateways", [])

    def get_hosts(self):
        return self.data.get("spec", {}).get("hosts", [])

    def get_selectors(self) -> dict[str, str]:
        return self.spec.selector


class DestinationRule(KObject):

    def __init__(self, data: dict):
        self.data: dict = data

    @staticmethod
    def from_dict(dictionary: dict):
        return DestinationRule(data=dictionary)

    def is_circuit_breaker(self) -> bool:
        return self.data.get("spec", {}).get("trafficPolicy", {}).get("connectionPool", None) is not None \
            # and self.data.get("spec", {}).get("trafficPolicy", {}).get("outlierDetection", None) is not None

    def get_host(self):
        return self.spec.host

    def get_timeout(self) -> str:
        return self.data.get("spec", {}).get("trafficPolicy", {}).get("connectionPool", {})\
            .get("tcp", {}).get("connectTimeout", None)


class Gateway(KObject):
    def __init__(self, data: dict):
        self.data: dict = data

    @staticmethod
    def from_dict(dictionary: dict):
        return Gateway(data=dictionary)

    def get_name(self):
        return self.data.get("metadata", {}).get("name", "")

    def get_all_host_exposed(self):
        result = []
        servers = self.data.get("spec", {}).get("servers", [])
        for server in servers:
            result += server.get("hosts", [])
        return result