from microfreshenerpp.kmodel.kube_istio import KubeVirtualService, KubeDestinationRule, KubeIstioGateway
from microfreshenerpp.kmodel.kube_networking import KubeService, KubeIngress
from microfreshenerpp.kmodel.kube_workload import KubePod, KubeDeployment, KubeReplicaSet, KubeStatefulSet


class KubeObjectFactory:
    kind_class_mapping = {
        "Pod": KubePod,
        "Service": KubeService,
        "Deployment": KubeDeployment,
        "ReplicaSet": KubeReplicaSet,
        "StatefulSet": KubeStatefulSet,
        "Ingress": KubeIngress,
        "VirtualService": KubeVirtualService,
        "DestinationRule": KubeDestinationRule,
        "Gateway": KubeIstioGateway
    }

    @staticmethod
    def build_object(object_dict, filename):
        object_kind = object_dict.get("kind", None)

        if not object_kind:
            return None

        kClass = KubeObjectFactory.kind_class_mapping.get(object_kind)

        if kClass is not None:
            kObject = kClass(data=object_dict)
            kObject.export_filename = filename

            return kObject

        return None
