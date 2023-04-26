#Cosa manca da spiegare
- Spiego bene cosa contiene ogni progetto: i file per testare il funzionamento del programma e il reference model (?)
- Devo dire cosa ogni progetto va a testare o entro troppo nel dettaglio? Almeno dire quanti diversi controlli e quali smell sono presenti in ogni progetto sì.

# Examples

In this folder are present four different examples for running and testing *microkure* functionalities. 
*MFDemo* and *Sock Shop* projects tests the extension and refactoring functionalities of microkure, while *multi-container-adapter* and *multi-container-sidecar* tests two failure cases in identifying *Multiple Services in One Pod* smell.

### MFDemo
MFDemo is a project designed for validating *microkure* which contains the microTOSCA definition of a demo system and its Kubernetes deployment. The application consists of 9 different microservices with 2 data stores, resulting in 32 nodes in the microTOSCA model and 25 Kubernetes resources defined.

### Sock Shop
[Sock Shop](https://github.com/microservices-demo/microservices-demo) a microservice-based demo application representing the user-facing part of e-commerce selling different types of socks. This system consists of 8 different microservices and 4 data stores, resulting in 26 nodes present in the graph and 29 Kubernetes resources defined.

The first microTOSCA model describing the project had been generated using [microMiner](https://github.com/di-unipi-socc/microMiner) with the Kubernetes deployment present in the project repository as input. Either the Kubernetes deployment and the microTOSCA model generated had been modified for introducing some architectural smells in the files, and the artifacts produced had been inserted in the _./data/examples/SockShop/reference-model_ folder.


### Multi container
The two [multi-container projects](https://github.com/kodestacked/k8s-multi-container-patterns) are implementation of the Kubernetes Adapter and Sidecar multi-container design pattern. The aim of this two projects is to test two particular cases during the identification of *Multiple Services in One Pod* smell, because the detector developed in *microFreshener-core* does not handle this cases and produces false positives.
