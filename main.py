from project.extender.extender import KubeExtender
from project.importer.yamlkimporter import YamlKImporter
from microfreshener.core.model.microtosca import MicroToscaModel

from project.kmodel.kube_cluster import KubeCluster

#TODO
'''
Tra i vari controlli effettuati ad es. per Gateway etc., manca quello sulle wildcard
'''

def main():
    # Importo il grafo MicroTosca
    fake_model = MicroToscaModel(name="fake model")

    # Importo le classi K8s
    import_directory = "./data/yaml_files/test"
    importer: YamlKImporter = YamlKImporter()
    cluster: KubeCluster = importer.Import(import_directory)

    # Effettuo le modifiche al grafo
    extender: KubeExtender = KubeExtender()
    modified_model: MicroToscaModel = extender.extend(model=fake_model, kube_cluster=cluster)

    # Lancio i detector

    # Mostro il grafo in output

main()
