from main import run

microtoscamodel = './demo/microTOSCA.yml'
kubedeploy = './demo/K8s'
ignore_config_path = None #TODO PENSARE ANCHE A QUESTO!!

# First we run only workers to get the model
output = "./out/demo"
refactoring = []
print("[DEMO] Started first run without refactoring selected")
run(kubedeploy, microtoscamodel, output, refactoring, ignore_config_path)

# Then we run selecting all refactoring
output = "./out/demo"
refactoring = ["all"]
print("[DEMO] Started second run without refactoring selected")
run(kubedeploy, microtoscamodel, output, refactoring, ignore_config_path)
