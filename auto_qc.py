import os, time, math, tempfile
from dataclasses import dataclass
from mathutils import Matrix, Vector
from . import sanitize_dmx


@dataclass
class CompileInputs:
    model_path: str
    mesh_paths: list[str]
    cdmaterials: str

    _pre_existing_qc: str or None = None

    @classmethod
    def from_qc_file(cls, path):
        raise NotImplementedError("QC parsing not implemented yet")

    @classmethod
    def from_mesh_file(cls, path):
        mesh_name, extension = os.path.splitext(os.path.basename(path))

        user = os.environ["USERNAME"].lower()
        model_path = "{}/{}.mdl".format(user, mesh_name)  # TODO: a more sensible default
        cdmaterials = "models/{}".format(user)

        # If it's a DMX, create a sanitized version first
        # TODO: check whether this is actually necessary depending on studiomdl's requirements
        if extension.lower() == ".dmx":
            mesh_path = TemporarySanitisedDMX(path)
        else:
            mesh_path = path

        return cls(model_path, [mesh_path], cdmaterials)

    @property
    def model_name(self):
        return os.path.splitext(os.path.basename(self.model_path))[0]

    # Returns a context manager, not the path itself
    def get_qc(self):
        if self._pre_existing_qc:
            return TemporaryButActuallyNotTemporaryFile(self._pre_existing_qc)
        else:
            qc_file = TemporaryQCFile(self)
            return qc_file


class TemporaryButActuallyNotTemporaryFile:
    def __init__(self, thing):
        self._thing = thing

    def __enter__(self):
        return self._thing

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class TemporarySanitisedDMX:
    def __init__(self, input_path):
        self._input_path = input_path
        self._output_path = None

    def __enter__(self):
        mesh_name, extension = os.path.splitext(os.path.basename(self._input_path))
        mesh_name = mesh_name + "_" + next(tempfile._get_candidate_names())
        print("Sanitising DMX", self._input_path, "using temp name", mesh_name)
        self._output_path = os.path.join(os.path.dirname(self._input_path), mesh_name + ".dmx")
        sanitize_dmx.external_sanitize_dmx(self._input_path, self._output_path)
        return self._output_path

    def __exit__(self, exc_type, exc_value, traceback):
        os.remove(self._output_path)


class TemporaryQCFile:
    def __init__(self, compile_inputs: CompileInputs):
        self._compile_inputs = compile_inputs
        self._path = None

    def __enter__(self):
        mesh_path = self._compile_inputs.mesh_paths[0]  # TODO: support multiple meshes
        # TODO: this sucks shit, find a different way
        if isinstance(mesh_path, TemporarySanitisedDMX):
            mesh_path = mesh_path.__enter__()
        mesh_name, _ = os.path.splitext(os.path.basename(mesh_path))

        qc_template = '$modelname "{model_path}"\n$cdmaterials {cdmaterials}\n$staticprop\n$model "studio" "{mesh_name}"\n$sequence idle "{mesh_name}" loop fps 1.00\n'
        qc_file = tempfile.NamedTemporaryFile(
            mode="w", dir=os.path.dirname(mesh_path), suffix=".qc", delete=False
        )
        qc_file.write(
            qc_template.format(
                model_path=self._compile_inputs.model_path,
                mesh_name=mesh_name,
                cdmaterials=self._compile_inputs.cdmaterials,
            )
        )
        qc_file.close()
        print("Creating temporary QC file", qc_file.name)
        self._path = qc_file.name

        return self._path

    def __exit__(self, exc_type, exc_value, traceback):
        os.remove(self._path)
        # TODO: this sucks shit, find a different way
        if isinstance(self._compile_inputs.mesh_paths[0], TemporarySanitisedDMX):
            self._compile_inputs.mesh_paths[0].__exit__(None, None, None)


# The following code is adapted from Blender Source Tools


class QcInfo:
    startTime = 0
    ref_mesh = None  # for VTA import
    a = None
    origin = None
    upAxis = 'Z'
    upAxisMat = None
    numSMDs = 0
    makeCamera = False
    in_block_comment = False
    jobName = ""
    root_filedir = ""

    def __init__(self):
        self.imported_smds = []
        self.vars = {}
        self.dir_stack = []

    def cd(self):
        return os.path.join(self.root_filedir, *self.dir_stack)


def appendExt(path, ext):
    if not path.lower().endswith("." + ext) and not path.lower().endswith(".dmx"):
        path += "." + ext
    return path


def printTimeMessage(start_time, name, job, typPe="SMD"):
    elapsedtime = int(time.time() - start_time)
    if elapsedtime == 1:
        elapsedtime = "1 second"
    elif elapsedtime > 1:
        elapsedtime = str(elapsedtime) + " seconds"
    else:
        elapsedtime = "under 1 second"

    print(type, name, "{}ed in".format(job), elapsedtime, "\n")


def getUpAxisMat(axis):
    if axis.upper() == 'X':
        return Matrix.Rotation(math.pi / 2, 4, 'Y')
    if axis.upper() == 'Y':
        return Matrix.Rotation(math.pi / 2, 4, 'X')
    if axis.upper() == 'Z':
        return Matrix()
    else:
        raise AttributeError("getUpAxisMat got invalid axis argument '{}'".format(axis))


# SMD types
REF = 0x1  # $body, $model, $bodygroup->studio (if before a $body or $model), $bodygroup, $lod->replacemodel
PHYS = 0x3  # $collisionmesh, $collisionjoints
ANIM = 0x4  # $sequence, $animation
FLEX = 0x6  # $model VTA


# Parses a QC file
def readQC(filepath, newscene, doAnim, makeCamera, rotMode, outer_qc=False) -> CompileInputs:
    filename = os.path.basename(filepath)
    filedir = os.path.dirname(filepath)

    def normalisePath(path):
        if os.path.sep == '/':
            path = path.replace('\\', '/')
        return os.path.normpath(path)

    if outer_qc:
        print("\nQC IMPORTER: now working on", filename)

        qc = self.qc = QcInfo()
        qc.startTime = time.time()
        qc.jobName = filename
        qc.root_filedir = filedir
        qc.makeCamera = makeCamera
        qc.animation_names = []
        if newscene:
            bpy.context.screen.scene = bpy.data.scenes.new(
                filename
            )  # BLENDER BUG: this currently doesn't update bpy.context.scene
        else:
            bpy.context.scene.name = filename
    else:
        qc = self.qc

    file = open(filepath, 'r')
    in_bodygroup = in_lod = in_sequence = False
    lod = 0
    for line_str in file:
        line = self.parseQuoteBlockedLine(line_str)
        if len(line) == 0:
            continue
        # print(line)

        # handle individual words (insert QC variable values, change slashes)
        i = 0
        for word in line:
            for var in qc.vars.keys():
                kw = "${}$".format(var)
                pos = word.lower().find(kw)
                if pos != -1:
                    word = word.replace(word[pos : pos + len(kw)], qc.vars[var])
            line[i] = word.replace("/", "\\")  # studiomdl is Windows-only
            i += 1

        # Skip macros
        if line[0] == "$definemacro":
            print("Warning: skipping macro for", filename)
            while line[-1] == "\\\\":
                line = self.parseQuoteBlockedLine(file.readline())

        # register new QC variable
        if line[0] == "$definevariable":
            qc.vars[line[1]] = line[2].lower()
            continue

        # dir changes
        if line[0] == "$pushd":
            if line[1][-1] != "\\":
                line[1] += "\\"
            qc.dir_stack.append(line[1])
            continue
        if line[0] == "$popd":
            try:
                qc.dir_stack.pop()
            except IndexError:
                pass  # invalid QC, but whatever
            continue

        # up axis
        if line[0] == "$upaxis":
            qc.upAxis = bpy.context.scene.vs.up_axis = line[1].upper()
            qc.upAxisMat = getUpAxisMat(line[1])
            continue

        # bones in pure animation QCs
        if line[0] == "$definebone":
            pass  # TODO

        def import_file(
            word_index, default_ext, smd_type, append='APPEND', layer=0, in_file_recursion=False
        ):
            path = os.path.join(qc.cd(), appendExt(normalisePath(line[word_index]), default_ext))

            if not in_file_recursion and not os.path.exists(path):
                return import_file(word_index, "dmx", smd_type, append, layer, True)

            if (
                not path in qc.imported_smds
            ):  # FIXME: an SMD loaded once relatively and once absolutely will still pass this test
                qc.imported_smds.append(path)
                self.append = append if qc.a else 'NEW_ARMATURE'

                # import the file
                self.num_files_imported += (self.readDMX if path.endswith("dmx") else self.readSMD)(
                    path, qc.upAxis, rotMode, False, smd_type, target_layer=layer
                )
            return True

        # meshes
        if line[0] in ["$body", "$model"]:
            import_file(2, "smd", REF)
            continue
        if line[0] == "$lod":
            in_lod = True
            lod += 1
            continue
        if in_lod:
            if line[0] == "replacemodel":
                import_file(2, "smd", REF, 'VALIDATE', layer=lod)
                continue
            if "}" in line:
                in_lod = False
                continue
        if line[0] == "$bodygroup":
            in_bodygroup = True
            continue
        if in_bodygroup:
            if line[0] == "studio":
                import_file(1, "smd", REF)
                continue
            if "}" in line:
                in_bodygroup = False
                continue

        # skeletal animations
        if in_sequence or (doAnim and line[0] in ["$sequence", "$animation"]):
            # there is no easy way to determine whether a SMD is being defined here or elsewhere, or even precisely where it is being defined
            num_words_to_skip = 2 if not in_sequence else 0
            for i in range(len(line)):
                if num_words_to_skip:
                    num_words_to_skip -= 1
                    continue
                if line[i] == "{":
                    in_sequence = True
                    continue
                if line[i] == "}":
                    in_sequence = False
                    continue
                if line[i] in [
                    "hidden",
                    "autolay",
                    "realtime",
                    "snap",
                    "spline",
                    "xfade",
                    "delta",
                    "predelta",
                ]:
                    continue
                if line[i] in ["fadein", "fadeout", "addlayer", "blendwidth", "node"]:
                    num_words_to_skip = 1
                    continue
                if line[i] in ["activity", "transision", "rtransition"]:
                    num_words_to_skip = 2
                    continue
                if line[i] in ["blend"]:
                    num_words_to_skip = 3
                    continue
                if line[i] in ["blendlayer"]:
                    num_words_to_skip = 5
                    continue
                # there are many more keywords, but they can only appear *after* an SMD is referenced

                if not qc.a:
                    qc.a = self.findArmature()
                if not qc.a:
                    print("Warning: no armature for line:", line_str.strip())
                    continue

                if line[i].lower() not in qc.animation_names:
                    if not qc.a.animation_data:
                        qc.a.animation_data_create()
                    last_action = qc.a.animation_data.action
                    import_file(i, "smd", ANIM, 'VALIDATE')
                    if line[0] == "$animation":
                        qc.animation_names.append(line[1].lower())
                    while i < len(line) - 1:
                        if line[i] == "fps" and qc.a.animation_data.action != last_action:
                            if 'fps' in dir(qc.a.animation_data.action):
                                qc.a.animation_data.action.fps = float(line[i + 1])
                        i += 1
                break
            continue

        # flex animation
        if line[0] == "flexfile":
            import_file(1, "vta", FLEX, 'VALIDATE')
            continue

        # naming shapes
        if qc.ref_mesh and line[0] in [
            "flex",
            "flexpair",
        ]:  # "flex" is safe because it cannot come before "flexfile"
            for i in range(1, len(line)):
                if line[i] == "frame":
                    shape = qc.ref_mesh.data.shape_keys.key_blocks.get(line[i + 1])
                    if shape and shape.name.startswith("Key"):
                        shape.name = line[1]
                    break
            continue

        # physics mesh
        if line[0] in ["$collisionmodel", "$collisionjoints"]:
            import_file(1, "smd", PHYS, 'VALIDATE', layer=10)  # FIXME: what if there are >10 LODs?
            continue

        # origin; this is where viewmodel editors should put their camera, and is in general something to be aware of
        if line[0] == "$origin":
            if qc.makeCamera:
                data = bpy.data.cameras.new(qc.jobName + "_origin")
                name = "camera"
            else:
                data = None
                name = "empty object"
            print("QC IMPORTER: created {} at $origin\n".format(name))

            origin = bpy.data.objects.new(qc.jobName + "_origin", data)
            bpy.context.scene.collection.objects.link(origin)

            origin.rotation_euler = Vector([pi / 2, 0, pi]) + Vector(
                getUpAxisMat(qc.upAxis).inverted().to_euler()
            )  # works, but adding seems very wrong!
            ops.object.select_all(action="DESELECT")
            origin.select_set(True)
            ops.object.transform_apply(rotation=True)

            for i in range(3):
                origin.location[i] = float(line[i + 1])
            origin.matrix_world = getUpAxisMat(qc.upAxis) @ origin.matrix_world

            if qc.makeCamera:
                bpy.context.scene.camera = origin
                origin.data.lens_unit = 'DEGREES'
                origin.data.lens = 31.401752  # value always in mm; this number == 54 degrees
                # Blender's FOV isn't locked to X or Y height, so a shift is needed to get the weapon aligned properly.
                # This is a nasty hack, and the values are only valid for the default 54 degrees angle
                origin.data.shift_y = -0.27
                origin.data.shift_x = 0.36
                origin.data.passepartout_alpha = 1
            else:
                origin.empty_display_type = 'PLAIN_AXES'

            qc.origin = origin

        # QC inclusion
        if line[0] == "$include":
            path = os.path.join(
                qc.root_filedir, normalisePath(line[1])
            )  # special case: ignores dir stack

            if not path.endswith(".qc") and not path.endswith(".qci"):
                if os.path.exists(appendExt(path, ".qci")):
                    path = appendExt(path, ".qci")
                elif os.path.exists(appendExt(path, ".qc")):
                    path = appendExt(path, ".qc")
            try:
                self.readQC(path, False, doAnim, makeCamera, rotMode)
            except IOError:
                self.warning(get_id("importer_err_qci", True).format(path))

    file.close()

    if qc.origin:
        qc.origin.parent = qc.a
        if qc.ref_mesh:
            size = min(qc.ref_mesh.dimensions) / 15
            if qc.makeCamera:
                qc.origin.data.display_size = size
            else:
                qc.origin.empty_display_size = size

    if outer_qc:
        printTimeMessage(qc.startTime, filename, "import", "QC")
    return self.num_files_imported
