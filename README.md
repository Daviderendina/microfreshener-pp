# microFreshener++

Introduzoine

---

### What microFreshener++ can do

- Potrei anche usare il workflow usato nella tesi?

---

### How to run 
microFreshener++ provides a CLi for using its functionalities. Before using it, is necessary to satisfy its requirements, by installing all its dependencies listed in the _requirements.txt_ files by using the command

```
$ pip install -r requirements.txt
```

After installing them, for running the tool the command 
```
$ python3 run.py --kube KUBE --model MODEL -r REFACTORING -ig IGNORE
```
where:
- KUBE is the path of the folder containing all the Kubernetes files of the application to analyze.
- MODEL is the path to the file which contains the MicroTosca model of the application to analyze.
- REFACTORING (optional) is used to specify one (or more) particular refactoring technique to apply. By default, all are applied.
- IGNORE (optional) is the ignore configuration, for specifying what smell, extension or refactoring needs to be ignored during the execution on a specific node. An example of ignore configuration can be observer in config/ignore_config_example.json, while all possible values are listed in config/ignore_config_values.json file




##### Configurations
- Parlo delle varie configurazioni che possono essere fatte