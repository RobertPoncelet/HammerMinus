import os, itertools
from srctools.game import Game
from srctools.filesys import FileSystemChain
from srctools.mdl import Model
from srctools.dmx import Element
from srctools.vmt import Material
from . import crowbar_settings
from .auto_qc import CompileInputs, TemporarySanitisedDMX


def get_game_filesystem(game: str) -> FileSystemChain:
    game_setup = crowbar_settings.get_game_setup(game)
    g = Game(os.path.dirname(game_setup["GamePathFileName"]))
    return g.get_filesystem()


def filesystem_contains_material(filesystem, model: Model, mat_name: str) -> bool:
    for mat_dir in model.cdmaterials:
        mat_dir = mat_dir.lstrip("/").rstrip("/")
        if mat_dir:
            mat_path = "/".join(["materials", mat_dir, mat_name + ".vmt"])
        else:
            mat_path = "/".join(["materials", mat_name + ".vmt"])
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

    original_mats = None

    output_dir = addon_path or os.path.dirname(
        crowbar_settings.get_game_setup(game)["GamePathFileName"]
    )

    mat_names = set(itertools.chain(*model.skins))
    for mat_name in mat_names:
        if not filesystem_contains_material(filesystem, model, mat_name):
            print("Couldn't find", mat_name, "- attempting to replace it")
            if original_mats is None:
                with TemporarySanitisedDMX(orig_mesh_path, clear_material_path=False) as clean_orig_mesh_path:
                    original_mats = get_original_mat_paths(clean_orig_mesh_path)
            try:
                parent_mat_path = next(
                    m for m in original_mats if os.path.splitext(os.path.basename(m))[0] == mat_name
                )
            except StopIteration:
                print("Couldn't find a parent material to copy from :(")
                continue

            parent_file = filesystem[parent_mat_path.replace(".vmat", ".vmt")]
            parent_file_contents = parent_file.open_str().read()
            new_mat = Material.parse(parent_file_contents)
            if new_mat.shader.lower() == "lightmappedgeneric":
                new_mat.shader = "VertexLitGeneric"
            else:
                print("Shader is", new_mat.shader)
            output_path = os.path.join(
                output_dir, "materials", compile_inputs.cdmaterials, mat_name + ".vmt"
            )

            print("Writing new material", output_path)
            if not os.path.isdir(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))
            with open(output_path, "w") as f:
                new_mat.export(f)
