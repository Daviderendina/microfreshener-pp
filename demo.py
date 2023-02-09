from main import run

#microtoscamodel = './demo/microTOSCA.yml'
microtoscamodel = './demo/sock-shop/injected/microTOSCA.yml'

#kubedeploy = './demo/K8s'
kubedeploy = './demo/sock-shop/injected'

#ignore_config_path = './demo/ignore_config.json'
ignore_config_path = None


# Then we run selecting all refactoring
output = "./out/demo"
refactoring = ["all"]
print("[DEMO] Started second run without refactoring selected")
run(kubedeploy, microtoscamodel, output, refactoring, ignore_config_path)
