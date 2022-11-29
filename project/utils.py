import re

from microfreshener.core.model import Root



def reorder_dict(dictionary: dict, attributes_order: list):
    for item in attributes_order:
        dictionary[item] = dictionary.pop(item)
    for key, item in dictionary.items():
        if key not in attributes_order:
            dictionary[key] = item
    return dictionary


def get_dict_key_by_value(dictionary: dict, search_value: str):
    try:
        dict_key = [key for key, value in dictionary.items() if value == search_value][0]
        return dict_key
    except:
        print(f"[utils.get_dict_key_by_value] - Value <{search_value}> not found in dictionary {dictionary}")


def check_kobject_node_name_match(kobject, tosca_node: Root, defining_object_fullname=""):
    # Case: tosca_node.name is <name>.<ns>
    if tosca_node.name == kobject.get_fullname():
        return True

    # Case: tosca_node.name is <name>
    if tosca_node.name == kobject.metadata.name:
        return True

    # Case: tosca_node.name is <name>.<ns>.<default>.<cluster>.<local>
    match_regex = f"{kobject.metadata.name}[.]{kobject.get_namespace()}[.]\w+[.]\w+[.]\w+"
    result = re.match(match_regex, tosca_node.name)
    if result and result.string == tosca_node.name:
        return True

    # Case: tosca_node.name is <container>.<name>.<ns>
    if defining_object_fullname != "":
        if f"{kobject.get_fullname()}.{defining_object_fullname}":
            return True

    return False
