from project.kmodel.kube_networking import KubeService, KubeIngress
from project.kmodel.kube_workload import KubePod, KubeDeployment, KubeReplicaSet, KubeStatefulSet


class KubeObjectFactory:
    kind_class_mapping = {
        "Pod": KubePod,
        "Service": KubeService,
        "Deployment": KubeDeployment,
        "ReplicaSet": KubeReplicaSet,
        "StatefulSet": KubeStatefulSet,
        "Ingress": KubeIngress
    }

    @staticmethod
    def build_object(object_dict, filename):
        object_kind = object_dict["kind"]

        kClass = KubeObjectFactory.kind_class_mapping.get(object_kind)

        if kClass is not None:
            kObject = kClass(data=object_dict)
            kObject.export_filename = filename

            return kObject

        return None
