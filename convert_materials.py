import os, itertools
from srctools.game import Game
from srctools.mdl import Model
from . import crowbar_settings
from .auto_qc import CompileInputs


def get_game_filesystem(game: str):
    game_setup = crowbar_settings.get_game_setup(game)
    g = Game(os.path.dirname(game_setup["GamePathFileName"]))
    return g.get_filesystem()


def filesystem_contains_material(filesystem, model: Model, mat_name: str):
    for mat_dir in model.cdmaterials:
        mat_dir = mat_dir.lstrip("/").rstrip("/")
        mat_path = "/".join(["materials", mat_dir, mat_name + ".vmt"])
        print("Looking for", mat_path)
        if mat_path in filesystem:
            print("Found", mat_path)
            return True
    return False
    

def convert_all_materials(compile_inputs: CompileInputs, game: str, addon_path=None):
    print("Converting materials for", compile_inputs.model_name)
    filesystem = get_game_filesystem(game)
    model = Model(filesystem, filesystem["models/" + compile_inputs.model_path])

    for mat_name in set(itertools.chain(*model.skins)):
        if not filesystem_contains_material(filesystem, model, mat_name):
            print("Couldn't find", mat_name)
            print(compile_inputs.model_path, "vs.", model.name)
            print(compile_inputs.cdmaterials, "vs.", model.cdmaterials)