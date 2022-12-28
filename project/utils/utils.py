import os


def create_folder(path):
    file_folder = f"./{os.path.dirname(path)}"
    if not os.path.exists(file_folder):
        os.makedirs(file_folder, 0o777)
