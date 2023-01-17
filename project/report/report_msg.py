import os

from project.kmodel.kube_istio import KubeIstio


def cannot_apply_refactoring_on_node_msg(refactoring_name, smell_name, node):
    return f"Cannot apply refactoring {refactoring_name} for smell {smell_name} on node '{node.name}': " \
           f"node type '{node.__class__.__name__}' not supported for refactoring "


def cannot_find_container_msg(service_node_name):
    return f"Cannot find KubeContainer associated to node '{service_node_name}'"


def found_wrong_type_object_msg(object_fullname, desired_class):
    return f"Found K8s object '{object_fullname}' which is not of type {desired_class}"


def compute_object_not_found_msg(compute_node_name):
    return f"Compute object named '{compute_node_name}' not found in cluster"


def change_call_to_service_msg(svc_name, k8s_service_name):
    return f"Direct call to Service '{svc_name}' must be changed for passing through the K8s generated Service:" \
           f" convert calls to hostname '{k8s_service_name}'"


def cannot_refactor_model_msg():
    return f"Is impossible to apply refactor on model"


def created_resource_msg(resource, resource_outfile):
    return f"Created K8s {_extract_kubernetes_name(resource)} named '{resource.fullname}' ({resource_outfile})"


def resource_modified_msg(resource, resource_outfile):
    return f"Modified K8s {_extract_kubernetes_name(resource)} named '{resource.fullname}' ({resource_outfile})"


def resource_deleted_msg(resource):
    return f"Deleted K8s {_extract_kubernetes_name(resource)} named '{resource.fullname}' from cluster"


def removed_exposing_params_msg(workload_fullname, resource_outfile):
    return f"Removed exposing attributed (hostNetworks and hostPorts) from object '{workload_fullname}' ({resource_outfile})"


def cannot_find_nodes_msg(node_names: list):
    return "Cannot find cluster object related to nodes: " + ''.join(node_names)

def exposed_node_port_change(old_exposed_object_name, expected_port, new_port):
    return f"The object {old_exposed_object_name} was exposed on port {expected_port}, but now is exposed on {new_port}." \
           f"Make sure to forward calls to the new port"

def _extract_kubernetes_name(resource):
    istio = ""
    if isinstance(resource, KubeIstio):
        istio = "Istio"

    return f"{istio}{resource.__class__.__name__[4:]}"
