# Hammer Minus

Hammer Minus is a Python toolset which aims to integrate Source 2 Hammer's powerful mesh editing tools into a Source 1 mapping workflow as smoothly as possible.

This works by having a Source 1 map addon with a Source 2 addon counterpart. Import the map from the former to the latter, use it as a reference to create the meshes, and export them to a folder - Hammer Minus will detect and take care of compiling them for Source 1 on the fly, materials and all.

![](demo.gif)

Currently this is largely untested and requires a fair amount of manual setup (see below), but I may get around to automating more of it. If you want to contribute, forks and pull requests are welcome!

## Features
* Automatic QC file generation and compilation, given an input mesh
* Automatic conversion of materials from `LightmappedGeneric` to `VertexLitGeneric` (Source 1 only)

## Roadmap Features
* Parsing Source 2 map files to automatically place the meshes in Source 1
* Automatic collision models
* Automatic conversion of Source 1 assets to Source 2 for use as reference in mesh editing

## Requirements

* Windows
* Python 3
* ZeqMacaw's [Crowbar](https://steamcommunity.com/groups/CrowbarTool) (Hammer Minus obtains game setup info from Crowbar's settings)
* TeamSpen210's [srctools](https://github.com/TeamSpen210/srctools)
* [Blender](https://www.blender.org/download/) with the [Blender Source Tools](http://steamreview.org/BlenderSourceTools/) installed (necessary for now in order to convert DMX files to a Source 1-compatible version)

## Usage

1. Ensure your Blender executable exists on your Windows `%PATH%` environment variable, and that your hammer_minus folder exists under the `%PYTHONPATH%`.
2. Open Crowbar and ensure your desired game has its paths set up correctly in the "Set Up Games" tab. If you want to export models to an addon folder instead of the game folder, specify this in the "Work folder" output option in the "Compile" tab. Then, close Crowbar.
3. Create a proxy version of your Source 1 addon for your Source 2 tools. I may automate this in the future, but for now you can use kristiker's [source1import](https://github.com/kristiker/source1import). Materials should share the same relative path in the Source 1 and Source 2 projects, except the .vmt/.vmat extension.
4. Navigate to whichever directory you'd like to export meshes from Source 2 Hammer, and run `python -m hammer_minus.minus_daemon --game <your desired game>` (the game name should match that of Crowbar's game setup). If you've specified a mapping tool in Crowbar, this will also be launched (unless you add `--no-start-mapping-tool`).
5. Launch Source 2 Hammer in the project you created in step 3, optionally import your Source 1 map file to use as reference, and create some meshes!
6. With a mesh selected, go to "File -> Export selected..." and save it as DMX format in the directory from step 4. Hammer Minus will then take care of compiling it for Source 1, converting materials, and moving the result to your addon directory.
7. Create a static or dynamic prop in Source 1 Hammer using the newly-created model from `models/<username>/<mesh name>.mdl`. Repeat the previous step to update its geometry. A version of Hammer which supports hotloading models, such as ficool2's [Hammer++](https://ficool2.github.io/HammerPlusPlus-Website/), is recommended for this.

## License

[MIT](LICENSE.txt)