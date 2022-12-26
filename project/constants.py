from datetime import datetime


OUTPUT_FOLDER = f"./out/{datetime.now().strftime('%Y%m%d_%H%M%S')}/"

REPORT_OUTPUT_FOLDER = f"{OUTPUT_FOLDER}/report"
DEPLOY_OUTPUT_FOLDER = f"{OUTPUT_FOLDER}/deploy"
TOSCA_OUTPUT_FOLDER = f"{OUTPUT_FOLDER}/microtosca"
GENERATED_DEPLOY_OUTPUT_FOLDER = f"{DEPLOY_OUTPUT_FOLDER}/auto_generated"


IGNORE_CONFIG_SCHEMA_FILE = "../schema/ignore_config_schema.json"

