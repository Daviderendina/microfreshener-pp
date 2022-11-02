import microfreshener.core.logging

from project.extender.extender import KubeExtender
from project.importer.yamlkimporter import YamlKImporter
from project.kmodel.kCluster import KCluster
from microfreshener.core.model.microtosca import MicroToscaModel


def main():
    # Importo il grafo MicroTosca
    fake_model = MicroToscaModel(name="fake model")

    # Importo le classi K8s
    import_directory = "./data/yaml_files/test"
    importer: YamlKImporter = YamlKImporter()
    cluster: KCluster = importer.Import(import_directory)

    # Effettuo le modifiche al grafo
    extender: KubeExtender = KubeExtender()
    modified_model: MicroToscaModel = extender.extend(model=fake_model, kube_cluster=cluster)

    # Lancio i detector

    # Mostro il grafo in output


main()
