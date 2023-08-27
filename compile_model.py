import argparse, os, subprocess, pathlib
from . import crowbar_settings

"""
We want to be able to compile a model as quickly and easily as possible.
Default setups and output directory (e.g. for addons) are specified through Crowbar.
TODO: add command line options to override these defaults.
The "path" argument can be a QC file, mesh file (SMD/DMX etc.) or directory.
If a QC is not supplied (in the path or its directory), one will be generated automatically.
"""

def get_compiled_files(studiomdl_output):
    lines = studiomdl_output.split("\n")
    files = set()
    for line in lines:
        for prefix in "writing ", "Generating optimized mesh ":
            if line.startswith(prefix):
                path = line.lstrip(prefix)
                path = path.lstrip("\"").rstrip("\":")
                files.add(path)
    return files


def move_compiled_files(compiled_files, game_path):
    game_path = os.path.abspath(game_path)
    parts = pathlib.Path(game_path).parts
    for f in compiled_files:



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--game", default=crowbar_settings.DEFAULT_GAME)
    args = parser.parse_args()

    if os.path.isdir(args.path):
        qcs = [f for f in os.listdir(args.path) if f.endswith(".qc")]
        if len(qcs) != 1:
            raise RuntimeError("Folder does not contain exactly one QC file")

        qc_path = os.path.join(args.path, qcs[0])
    else:
        model_name, extension = os.path.splitext(os.path.basename(args.path))
        if extension != "qc":
            raise NotImplementedError  # TODO

        qc_path = args.path

    game_setup = crowbar_settings.get_game_setup(args.game)
    print("Compiling", qc_path, "for", game_setup["GameName"])
    cmd_list = [
        game_setup["CompilerPathFileName"],
        "-game",
        os.path.dirname(game_setup["GamePathFileName"]),
    ]
    if crowbar_settings.nop4:
        cmd_list.append("-nop4")
    cmd_list.append(qc_path)

    print(" ".join(cmd_list))
    result = subprocess.check_output(cmd_list, text=True)
    print(result)

    if not crowbar_settings.compile_output_dir:
        quit()

    move_compiled_files(get_compiled_files(), os.path.dirname(game_setup["GamePathFileName"]))