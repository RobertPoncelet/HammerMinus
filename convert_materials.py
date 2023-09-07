import os, itertools
from srctools.game import Game
from srctools.filesys import FileSystemChain
from srctools.mdl import Model
from srctools.dmx import Element
from . import crowbar_settings
from .auto_qc import CompileInputs, TemporarySanitisedDMX


def get_game_filesystem(game: str) -> FileSystemChain:
    game_setup = crowbar_settings.get_game_setup(game)
    g = Game(os.path.dirname(game_setup["GamePathFileName"]))
    return g.get_filesystem()


def filesystem_contains_material(filesystem, model: Model, mat_name: str) -> bool:
    for mat_dir in model.cdmaterials:
        mat_dir = mat_dir.lstrip("/").rstrip("/")
        mat_path = "/".join(["materials", mat_dir, mat_name + ".vmt"])
        print("Looking for", mat_path)
        if mat_path in filesystem:
            print("Found", mat_path)
            return True
    return False


def get_original_mat_paths(orig_mesh_path: str) -> set[str]:
    filename, extension = os.path.splitext(orig_mesh_path)
    if extension.lower() != ".dmx":
        raise NotImplementedError("Only DMX is supported currently")

    with open(orig_mesh_path, "rb") as f:
        dmx, format_name, format_version = Element.parse(f)

    paths = set()
    model = dmx["model"].val_elem
    for dag_node in model["children"].iter_elem():
        shape = dag_node["shape"].val_elem
        for face_set in shape["faceSets"].iter_elem():
            material = face_set["material"].val_elem
            mat_path = material["mtlName"].val_string
            paths.add(mat_path)

    return paths


def convert_all_materials(
    compile_inputs: CompileInputs, orig_mesh_path: str, game: str, addon_path=None
):
    print("Converting materials for", compile_inputs.model_name)
    filesystem = get_game_filesystem(game)
    model = Model(filesystem, filesystem["models/" + compile_inputs.model_path])

    with TemporarySanitisedDMX(orig_mesh_path, clear_material_path=False) as clean_orig_mesh_path:
        original_mats = get_original_mat_paths(clean_orig_mesh_path)
    print("Original materials: ", original_mats)

    for mat_name in set(itertools.chain(*model.skins)):
        if not filesystem_contains_material(filesystem, model, mat_name):
            print("Couldn't find", mat_name)
            print(compile_inputs.model_path, "vs.", model.name)
            print(compile_inputs.cdmaterials, "vs.", model.cdmaterials)
