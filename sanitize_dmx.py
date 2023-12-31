import argparse, os, sys, subprocess


def external_sanitize_dmx(
    input_path: str, output_path: str, engine_path: str = None, clear_material_path: bool = True
):
    cmd_list = [
        "blender",
        "-b",  # background
        "--python-use-system-env",
        "--enable-autoexec",
        "--python-exit-code",
        "255",
        "--python",
        __file__,
        "--",
        input_path,
        output_path,
    ]
    if engine_path:
        cmd_list.append("--engine-path")
        cmd_list.append(engine_path)
    if not clear_material_path:
        cmd_list.append("--no-clear-material-path")
    subprocess.run(cmd_list).check_returncode()


def main(
    input_path: str, output_path: str, engine_path: str = None, clear_material_path: bool = True
):
    import bpy

    if not hasattr(bpy.ops.import_scene, "smd"):
        raise RuntimeError("DMX export not available; is the Blender Source Tools addon installed?")

    bpy.ops.import_scene.smd(filepath=input_path)

    input_name, input_ext = os.path.splitext(os.path.basename(input_path))
    output_name, output_ext = os.path.splitext(os.path.basename(output_path))
    assert output_ext.lower() == ".dmx"
    bpy.data.collections[input_name].name = output_name

    bpy.context.scene.vs.export_format = "DMX"
    bpy.context.scene.vs.dmx_encoding = "2"
    bpy.context.scene.vs.dmx_format = "1"
    bpy.context.scene.vs.export_path = os.path.dirname(output_path)
    if clear_material_path:
        bpy.context.scene.vs.material_path = ""
    bpy.ops.export_scene.smd(export_scene=True)

    # bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]

    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_path")
    parser.add_argument("--engine-path")
    parser.add_argument(
        "--clear-material-path", action=argparse.BooleanOptionalAction, default=True
    )
    args = parser.parse_args(argv)

    main(
        args.input_path,
        args.output_path,
        args.engine_path,
        clear_material_path=args.clear_material_path,
    )
