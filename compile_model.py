import argparse, os, subprocess, pathlib
from . import crowbar_settings, auto_qc

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


def move_compiled_files(compiled_files, game_path, destination):
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

        if os.path.exists(output_path):
            print("OVERWRITING", output_path)
            os.remove(output_path)
        os.rename(input_path, output_path)


def compile_qc(qc_path, game_setup):
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
    #result = subprocess.run(cmd_list)
    result = subprocess.check_output(cmd_list, text=True)
    print(result)
    return result


def main(path, game=crowbar_settings.DEFAULT_GAME):
    game_setup = crowbar_settings.get_game_setup(game)

    if os.path.isdir(path):
        qcs = [f for f in os.listdir(path) if f.endswith(".qc")]
        if len(qcs) != 1:
            raise RuntimeError("Folder does not contain exactly one QC file")

        qc_path = os.path.join(path, qcs[0])
        result = compile_qc(qc_path, game_setup)
    else:
        model_name, extension = os.path.splitext(os.path.basename(path))
        if extension == ".qc":
            result = compile_qc(path, game_setup)
        else:  # Let's assume it's a mesh file like SMD
            with auto_qc.TemporaryQC(path) as qc_file:
                result = compile_qc(qc_file.path, game_setup)

    if crowbar_settings.compile_output_dir:
        move_compiled_files(
            get_compiled_files(result),
            os.path.dirname(game_setup["GamePathFileName"]),
            crowbar_settings.compile_output_dir,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--game", default=crowbar_settings.DEFAULT_GAME)
    args = parser.parse_args()

    main(args.path, args.game)
