from kubernetes.client.models import V1ObjectMeta

from project.kmodel.kObject import KObject


class KMetadata(V1ObjectMeta, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        metadata = KMetadata()
        metadata.set_all_attributes_except(dictionary)
        metadata.set_attribute_order(dictionary)

        return metadata
