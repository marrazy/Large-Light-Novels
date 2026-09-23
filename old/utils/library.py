import os
import shutil

def switch_library(name):
    path = f'./vectordb/{name}'
    os.makedirs(path, exist_ok=True)
    return path

def save_current_library(name):
    if os.path.exists("./vectordb/current"):
        shutil.copytree("./vectordb/current", f"./vectordb/{name}", dirs_exist_ok=True)

def set_active_library(name):
    if os.path.exists(f"./vectordb/{name}"):
        shutil.copytree(f"./vectordb/{name}", "./vectordb/current", dirs_exist_ok=True)

def create_new_library(name):
    path = f"./vectordb/{name}"
    os.makedirs(path, exist_ok=True)
    return path