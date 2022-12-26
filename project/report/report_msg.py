

def cannot_apply_refactoring_on_node_msg(refactoring_name, smell_name, node):
    return f"Cannot apply refactoring {refactoring_name} for smell {smell_name} on node {node.name}: " \
           f"node type {node.__class__.__name__} not supported for refactoring "


def cannot_find_container_msg(service_node_name):
    return f"Cannot find KubeContainer associated to node {service_node_name}"


def found_wrong_type_object_msg(object_fullname, desired_class):
    return f"Found K8s object {object_fullname} which is not of type {desired_class}" #TODO migliorare msg


def compute_object_not_found_msg(compute_node_name):
    return f"Compute object named {compute_node_name} not found in cluster"


def change_call_to_service_msg(svc_name, k8s_service_name):
    return f"Direct call to Service {svc_name} must be changed for passing through the K8s Service {k8s_service_name}"
    #TODO rivedere