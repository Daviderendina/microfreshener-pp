from enum import Enum
from main import run


class PROJECTS(Enum):
    MYDEMO = "mfdemo",
    SOCKSHOP = "sockshop",
    ADAPTER = "adapter",
    SIDECAR = "sidecar"


files = {
    PROJECTS.MYDEMO: {
        "model": "./demo/mydemo/microTOSCA.yml",
        "kube": "./demo/mydemo/kubernetes",
    },
    PROJECTS.SOCKSHOP: {
        "model": "./demo/sock-shop/injected/microTOSCA.yml",
        "kube": "./demo/sock-shop/injected"
    },
    PROJECTS.ADAPTER: {
        "model": "./demo/multi-container-adapter/microTOSCA.yml",
        "kube": "./demo/multi-container-adapter",
    },
    PROJECTS.SIDECAR: {
        "model": "./demo/multi-container-sidecar/microTOSCA.yml",
        "kube": "./demo/multi-container-sidecar",
    },
}

current_project = PROJECTS.SIDECAR


ignore_config_path = None #'./demo/ignore_config.json'


# Then we run selecting all refactoring
output = "./out/demo"
refactoring = ["all"]
print("[DEMO] Started second run without refactoring selected")
run(
    microtoscamodel=files[current_project]["model"],
    kubedeploy=files[current_project]["kube"],
    output=output,
    refactoring=refactoring,
    ignore_config_path=ignore_config_path)
