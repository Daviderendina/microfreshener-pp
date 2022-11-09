import six
from microfreshener.core.errors import *
from microfreshener.core.model import *
from microfreshener.core.model.nodes import *


# TODO da rimuovere quando pubblico su pip il package
class Compute(Service):

    def __init__(self, name):
        super(Compute, self).__init__(name)

    def __str__(self):
        return '{} ({})'.format(self.name, 'compute')


class DeployedOn(Relationship):

    def __init__(self, source, target, id=None):
        if isinstance(source, Service) and isinstance(target, Compute):
            super().__init__(source, target, id)
        else:
            raise MicroToscaModelError(
                f"DeployedOn relationship cannot be created from {source} to {target}. {type(source).__name__}")

    def __str__(self):
        return 'DeployedOn({})'.format(super(DeployedOn, self).__str__())

    def __repr__(self):
        return 'DeployedOn({})'.format(super(DeployedOn, self).__repr__())

    # def __eq__(self, other):
    #     return super(InteractsWith, self).__eq__(other) and self.timeout == other.timeout and self.circuit_breaker == other.circuit_breaker and self.dynamic_discovery == other.dynamic_discovery

    def to_dict(self):
        # return {'source': str(self.source), 'target': str(self.target)}
        return {'source': self.source.name, 'target': self.target.name, "type": "deploment"}
