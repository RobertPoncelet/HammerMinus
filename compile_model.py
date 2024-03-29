import argparse, os, subprocess, pathlib
from . import crowbar_settings
from .auto_qc import CompileInputs
from .convert_materials import convert_all_materials

"""
We want to be able to compile a model as quickly and easily as possible.
Default setups and output directory (e.g. for addons) are specified through Crowbar.
TODO: add command line options to override these defaults.
The "path" argument can be a QC file, mesh file (SMD/DMX etc.) or directory.
If a QC is not supplied (in the path or its directory), one will be generated automatically.
"""


def get_compiled_files(studiomdl_output: str) -> set[str]:
    lines = studiomdl_output.split("\n")
    files = set()
    for line in lines:
        for prefix in "writing ", "Generating optimized mesh ":
            if line.startswith(prefix):
                path = line.lstrip(prefix)
                path = path.lstrip("\"").rstrip("\":\r")
                files.add(path)
    return files


def move_compiled_files(compiled_files: set[str], game_path: str, destination: str):
    print("Moving compiled files from {} to {}".format(game_path, destination))
    game_path = os.path.abspath(game_path)
    parts = pathlib.Path(game_path).parts
    for input_path in compiled_files:
        input_path_parts = pathlib.Path(os.path.abspath(input_path)).parts
        same = 0
        for i in range(len(parts)):
            if input_path_parts[i] == parts[i]:
                same += 1
            else:
                break

        relative_path = os.path.join(*input_path_parts[same:])
        output_path = os.path.join(destination, relative_path)
        print("{} -> {}".format(input_path, output_path))

        if not os.path.isdir(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        elif os.path.exists(output_path):
            print("OVERWRITING", output_path)
            os.remove(output_path)
        os.rename(input_path, output_path)


def find_compile_inputs_from_path(path: str) -> CompileInputs:
    if os.path.isdir(path):
        qcs = [f for f in os.listdir(path) if f.lower().endswith(".qc")]
        meshes = [
            f for f in os.listdir(path) if f.lower().endswith(".smd") or f.lower().endswith(".dmx")
        ]
        if len(qcs) > 1:
            raise FileExistsError("Folder contains more than one QC file")
        elif len(qcs) == 1:
            compile_inputs = CompileInputs.from_qc_file(os.path.join(path, qcs[0]))
        elif len(meshes) > 1:
            raise FileExistsError("Folder contains more than one mesh")
        else:
            compile_inputs = CompileInputs.from_mesh_file(os.path.join(path, meshes[0]))
    else:
        filename, extension = os.path.splitext(os.path.basename(path))
        if extension.lower() == ".qc":
            compile_inputs = CompileInputs.from_qc_file(path)
        else:  # Let's assume it's a mesh file like SMD
            compile_inputs = CompileInputs.from_mesh_file(path)
    return compile_inputs


def compile_qc(qc_path: str, game_setup: dict) -> set[str]:
    cmd_list = [
        game_setup["CompilerPathFileName"],
        "-game",
        os.path.dirname(game_setup["GamePathFileName"]),
    ]
    if crowbar_settings.nop4:
        cmd_list.append("-nop4")
    cmd_list.append(qc_path)

    print(" ".join(cmd_list))
    result = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.check_returncode()
    output = result.stdout.decode()

    print(output)
    return get_compiled_files(output)


def main(
    path: str,
    game=crowbar_settings.DEFAULT_GAME,
    addon_path: str = None,
    do_convert_materials: bool = False,
):
    addon_path = addon_path or crowbar_settings.compile_output_dir
    if addon_path and not os.path.isdir(addon_path):
        raise ValueError("Addon path", addon_path, "does not exist")

    if do_convert_materials:
        filename, extension = os.path.splitext(path)
        if extension != ".dmx":
            raise ValueError("Converting materials for non-DMX meshes is currently unsupported")

    game_setup = crowbar_settings.get_game_setup(game)

    compile_inputs = find_compile_inputs_from_path(path)

    print("Compiling", compile_inputs.model_name, "for", game_setup["GameName"])
    with compile_inputs.get_qc_with_dependencies() as qc_path:
        compiled_files = compile_qc(qc_path, game_setup)

        if addon_path:
            move_compiled_files(
                compiled_files,
                os.path.dirname(game_setup["GamePathFileName"]),
                addon_path,
            )

        if do_convert_materials:
            convert_all_materials(compile_inputs, path, game)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # TODO: add help to arguments
    parser.add_argument("path")
    parser.add_argument("--game", default=crowbar_settings.DEFAULT_GAME)
    parser.add_argument("--addon-path", default=None)
    parser.add_argument('--convert-materials', action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    main(args.path, args.game, args.addon_path, args.convert_materials)
