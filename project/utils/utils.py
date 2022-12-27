import os
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


def check_ports_match(k_service, k_container):
    #TODO rimuovere da qui e usare l'altro
    service_ports = []
    for port in k_service.ports:
        port.get("get", "-1")

    for port in k_container.ports:
        if port["containerPort"] in service_ports:
            return False
    return True


def create_folder(path):
    file_folder = f"./{os.path.dirname(path)}"
    if not os.path.exists(file_folder):
        os.makedirs(file_folder, 0o777)
