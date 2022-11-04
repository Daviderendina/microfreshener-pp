from project.utils import *
import six


def parse_list(destination_class, dictionary_list):
    object_list = list()

    for dictionary_obj in dictionary_list:
        object_list.append(destination_class.from_dict(dictionary_obj))

    return object_list


class KObject:
    # TODO usare il costruttore qui?
    export_filename = "no_name_set.yaml"
    export_attribute_order = []

    DEFAULT_NAMESPACE = "default"

    #    id = -1

    def to_dict_yaml(self):
        result = {}

        ordered_dict = reorder_dict(
            dictionary=self.attribute_map,
            attributes_order=self.export_attribute_order
        )

        for attr, attr_yaml_name in six.iteritems(ordered_dict):

            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr_yaml_name] = list(map(
                    lambda x: x.to_dict_yaml() if hasattr(x, "to_dict_yaml") else x,
                    value
                ))
            elif isinstance(value, KObject):
                val = value.to_dict_yaml()
                if val is not None:
                    result[attr_yaml_name] = val
            elif isinstance(value, dict):
                result[attr_yaml_name] = dict(map(
                    lambda item: (item[0], item[1].to_dict_yaml())
                    if hasattr(item[1], "to_dict_yaml") else item,
                    value.items()
                ))
            elif value is not None:
                result[attr_yaml_name] = value

        return result

    def set_attribute_order(self, dictionary: dict):
        self.export_attribute_order = list(
            map(
                lambda x: get_dict_key_by_value(self.attribute_map, x),
                dictionary.keys()
            ))

    def set_all_attributes_except(self, dictionary: dict, except_attributes: list = []):
        for key, value in dictionary.items():
            attribute = get_dict_key_by_value(self.attribute_map, key)
            if hasattr(self, attribute) and key not in except_attributes:
                setattr(self, attribute, dictionary.get(key, ""))

    def get_name_dot_namespace(self):
        return (self.metadata.name if self.metadata.name else "") + "." + self.get_namespace()
        #return self.metadata.name + "." + self.get_namespace()

    def get_namespace(self):
        return self.metadata.namespace if self.metadata.namespace else self.DEFAULT_NAMESPACE

