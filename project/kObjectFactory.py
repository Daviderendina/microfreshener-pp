from project.kmodel.kObject import KObject  # , IDGenerator
from project.kmodel.kIngress import KIngress
from project.kmodel.kDeployment import KDeployment
from project.kmodel.kPod import KPod
from project.kmodel.kReplicaSet import KReplicaSet
from project.kmodel.kService import KService
from project.kmodel.kStatefulSet import KStatefulSet


class KObjectFactory:
    kind_class_mapping = {
        "Pod": KPod,
        "Service": KService,
        "Deployment": KDeployment,
        "ReplicaSet": KReplicaSet,
        "StatefulSet": KStatefulSet,
        "Ingress": KIngress
    }

    @staticmethod
    def build_object(object_dict, filename):
        object_kind = object_dict["kind"]

        kClass = KObjectFactory.kind_class_mapping.get(object_kind)

        if kClass is not None:
            kObject: KObject = kClass.from_dict(object_dict)
            kObject.export_filename = filename

            return kObject

        return None
