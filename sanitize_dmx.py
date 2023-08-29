import os


def blender_sanitize_dmx(dmx_path):
    import bpy

    if not hasattr(bpy.ops.export_scene, "smd"):
        raise RuntimeError("DMX export not available; is the Blender Source Tools addon installed?")

    # bpy.ops.wm.read_factory_settings(use_empty=True)

    bpy.ops.import_scene.smd(filepath=dmx_path)

    bpy.context.scene.vs.export_format = "DMX"
    bpy.context.scene.vs.export_path = os.path.dirname(dmx_path)
    bpy.ops.export_scene.smd()


# from hammer_minus import sanitize_dmx; sanitize_dmx.blender_sanitize_dmx(r"F:\Google Drive\sourceModelCompilation\juncture_s2_test\airport_test_dmx.dmx")
