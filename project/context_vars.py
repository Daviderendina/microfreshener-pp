from datetime import datetime

from project.constants import ImportExportConstants

run_identifier = datetime.now().strftime("%Y%m%d_%H%M%S")
#TODO mi invento qualcosa di meglio?

output_folder = f"{ImportExportConstants.export_directory}/{run_identifier}/"
