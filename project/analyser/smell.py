from microfreshener.core.analyser.costants import SMELL_MULTIPLE_SERVICES_IN_ONE_CONTAINER, REFACTORING_SPLIT_SERVICES
from microfreshener.core.analyser.smell import NodeSmell

#TODO lo metto qui o con gli altri?


class MultipleServicesInOneContainerSmell(NodeSmell):
    name: str = SMELL_MULTIPLE_SERVICES_IN_ONE_CONTAINER

    def __init__(self, node):
        super(MultipleServicesInOneContainerSmell, self).__init__(self.name, node)

    def __str__(self):
        return 'MultipleServicesInOneContainerSmell({})'.format(super(NodeSmell, self).__str__())

    def to_dict(self):
        sup_dict = super(MultipleServicesInOneContainerSmell, self).to_dict()
        return {**sup_dict, **{"refactorings": [
            {"name": REFACTORING_SPLIT_SERVICES, "description": "Split containers in two pods"},
        ]}}