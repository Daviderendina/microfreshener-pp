from microfreshener.core.analyser.sniffer import NodeSmellSniffer
from microfreshener.core.helper.decorator import visitor
from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Compute

from project.analyser.smell import MultipleServicesInOneContainerSmell


class MultipleServicesInOneContainerSmellSniffer(NodeSmellSniffer):

    def __str__(self):
        return 'MultipleServicesInOneContainerSmellSniffer({})'.format(super(NodeSmellSniffer, self).__str__())

    @visitor(Compute)
    def snif(self, Compute) -> MultipleServicesInOneContainerSmell:
        smell = MultipleServicesInOneContainerSmell(Compute)
        nodes = set(link.source for link in Compute.incoming_interactions)
        if (len(nodes) > 1):
            for link in Compute.incoming_interactions:
                smell.addLinkCause(link)
                smell.addNodeCause(link.source) #TODO serve?
        return smell

    @visitor(MicroToscaModel)
    def snif(self, micro_model):
        print("visiting all the nodes in the graph")
