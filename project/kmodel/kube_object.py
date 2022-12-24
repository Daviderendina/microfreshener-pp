
class KubeObject:
    DEFAULT_NAMESPACE = "default"

    def __init__(self, data: dict):
        self.data: dict = data
        self.shortname = ""

    @property
    def name(self):
        return self.data.get("metadata", {}).get("name", "")

    @property
    def namespace(self):
        return self.data.get("metadata", {}).get("namespace", self.DEFAULT_NAMESPACE)

    @property
    def fullname(self):
        return f"{self.name}.{self.namespace}"

    @property
    def typed_fullname(self):
        return f"{self.fullname}.{self.shortname}"

    def set_labels(self, labels: dict):
        if self.data.get("metadata", {}).get("labels", None):
            self.data["metadata"]["labels"].update(labels)
        else:
            self.data["metadata"]["labels"] = labels
