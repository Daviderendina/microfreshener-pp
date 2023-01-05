from main import run

microtoscamodel = './demo/microTOSCA.yml'
microtoscamodel_names = './demo/microTOSCA-names.yml'

kubedeploy = './demo/K8s'
ignore_config_path = None

# Then we run selecting all refactoring
output = "./out/demo"
refactoring = ["all"]
print("[DEMO] Started second run without refactoring selected")
run(kubedeploy, microtoscamodel_names, output, refactoring, ignore_config_path)
