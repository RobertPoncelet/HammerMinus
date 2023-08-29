import argparse, os, sys


def blender_sanitize_dmx(input_path, output_path, engine_path=None):
    import bpy

    if not hasattr(bpy.ops.export_scene, "smd"):
        raise RuntimeError("DMX export not available; is the Blender Source Tools addon installed?")
    import io_scene_valvesource

    # bpy.ops.wm.read_factory_settings(use_empty=True)

    bpy.ops.import_scene.smd(filepath=input_path)

    input_name, input_ext = os.path.splitext(os.path.basename(input_path))
    output_name, output_ext = os.path.splitext(os.path.basename(output_path))
    assert output_ext.lower() == ".dmx"
    bpy.data.collections[input_name].name = output_name

    bpy.context.scene.vs.export_format = "DMX"
    bpy.context.scene.vs.dmx_encoding = "2"
    bpy.context.scene.vs.dmx_format = "1"
    if engine_path:
        bpy.context.scene.vs.engine_path = os.path.dirname(engine_path)
    else:
        # TODO: is this needed?
        io_scene_valvesource.utils._StateMeta._engineBranch = (
            io_scene_valvesource.utils.dmx_versions_source1["Source2009"]
        )
    bpy.context.scene.vs.export_path = os.path.dirname(output_path)
    bpy.ops.export_scene.smd()

    bpy.ops.wm.quit_blender()


# from hammer_minus import sanitize_dmx; sanitize_dmx.blender_sanitize_dmx(r"F:\Google Drive\sourceModelCompilation\juncture_s2_test\airport_test_dmx.dmx", r"F:\Google Drive\sourceModelCompilation\juncture_s2_test\fuck.dmx")

if __name__ == "__main__":
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]

    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_path")
    parser.add_argument("--engine_path")
    args = parser.parse_args(argv)

    blender_sanitize_dmx(args.input_path, args.output_path, args.engine_path)