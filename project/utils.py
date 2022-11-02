import os


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

'''
def find_dict_match(d1: dict, d2: dict):
    for k, v in d1.items():
        if d2.get(k) == v:
            return True
    return False


def create_folder(filename):
    file_folder = os.path.dirname(filename)
    if not os.path.exists(file_folder):
        os.makedirs(file_folder, 0o777)
'''