from microfreshener.core.model import MicroToscaModel


class NameAdjuster:

    def __init__(self, name_mapping: dict):
        self.name_mapping = name_mapping

    def adjust(self, model: MicroToscaModel):
        for node in list(model.nodes):
            old_name = self.name_mapping.get(node.name, None)

            if old_name:
                model.rename_node(node, old_name)

        return model
