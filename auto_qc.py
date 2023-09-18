import os, time, math, tempfile
from dataclasses import dataclass
from mathutils import Matrix, Vector
from . import sanitize_dmx


@dataclass
class CompileInputs:
    model_path: str
    mesh_paths: list[str]
    cdmaterials: str

    _temp_meshes: list

    _pre_existing_qc: str or None = None

    @classmethod
    def from_qc_file(cls, path: str):
        raise NotImplementedError("QC parsing not implemented yet")

    @classmethod
    def from_mesh_file(cls, path: str):
        mesh_name, extension = os.path.splitext(os.path.basename(path))

        # TODO: more sensible defaults
        user = os.environ["USERNAME"].lower()
        model_path = "{}/{}.mdl".format(user, mesh_name)
        cdmaterials = "models/{}/autoqc".format(user)

        # If it's a DMX, create a sanitized version first
        # TODO: check whether this is actually necessary depending on studiomdl's requirements
        if extension.lower() == ".dmx":
            temp_meshes = [TemporarySanitisedDMX(path)]
            mesh_paths = []
        else:
            temp_meshes = []
            mesh_paths = [path]

        return cls(model_path, mesh_paths, cdmaterials, _temp_meshes=temp_meshes)

    @property
    def model_name(self):
        return os.path.splitext(os.path.basename(self.model_path))[0]

    # Returns a context manager, not the path itself
    def get_qc_with_dependencies(self):
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
    def __init__(self, input_path: str, clear_material_path: bool = True):
        self._input_path = input_path
        self._clear_material_path = clear_material_path
        mesh_name, extension = os.path.splitext(os.path.basename(self._input_path))
        mesh_name = mesh_name + "_" + next(tempfile._get_candidate_names())
        self._output_path = os.path.join(os.path.dirname(self._input_path), mesh_name + ".dmx")

    def __enter__(self) -> str:
        print("Sanitising DMX", self._input_path, "using temp path", self._output_path)
        sanitize_dmx.external_sanitize_dmx(
            self._input_path, self._output_path, clear_material_path=self._clear_material_path
        )
        return self._output_path

    def __exit__(self, exc_type, exc_value, traceback):
        os.remove(self._output_path)


class TemporaryQCFile:
    def __init__(self, compile_inputs: CompileInputs):
        self._compile_inputs = compile_inputs
        self._path = None

    def __enter__(self) -> str:
        # TODO: support multiple meshes
        if self._compile_inputs._temp_meshes:
            mesh_path = self._compile_inputs._temp_meshes[0].__enter__()
            self._compile_inputs.mesh_paths.append(mesh_path)
        else:
            mesh_path = self._compile_inputs.mesh_paths[0]

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
        for temp_mesh in self._compile_inputs._temp_meshes:
            temp_mesh.__exit__(None, None, None)