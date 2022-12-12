
class KubeObject:
    DEFAULT_NAMESPACE = "default"

    def __init__(self, data: dict):
        self.data: dict = data

    @property
    def name(self):
        return self.data.get("metadata", {}).get("name", "")

    def get_namespace(self):
        return self.data.get("metadata", {}).get("namespace", self.DEFAULT_NAMESPACE)

    def get_fullname(self):
        return f"{self.name}.{self.get_namespace()}"

    def set_labels(self, labels: dict):
        if self.data.get("metadata", {}).get("labels", None):
            self.data["metadata"]["labels"].update(labels)
        else:
            self.data["metadata"]["labels"] = labels
