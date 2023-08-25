import os
from xml.etree import ElementTree

zm_path = os.path.join(os.environ["APPDATA"], "ZeqMacaw")
is_crowbar_dir = lambda d: os.path.isdir(os.path.join(zm_path, d)) and d.startswith("Crowbar ")
crowbar_versions = [d for d in os.listdir(zm_path) if is_crowbar_dir(d)]
chosen_version = max(crowbar_versions)
print("Using settings from", chosen_version)
chosen_dir = os.path.join(zm_path, chosen_version)

cb_settings_tree = ElementTree.parse(os.path.join(chosen_dir, "Crowbar Settings.xml"))
root = cb_settings_tree.getroot()
game_setups = root.find("GameSetups")
library_paths = root.find("SteamLibraryPaths")

library_path_macros = {}
for lib_path in library_paths:
    search = lib_path.find("Macro").text
    replace = lib_path.find("LibraryPath").text
    library_path_macros[search] = replace

DEFAULT_GAME = object()

def text_setting(name):
    return root.find(name).text

# Compile options
default_game_index = int(text_setting("CompileGameSetupSelectedIndex"))
nop4 = text_setting("CompileOptionNoP4IsChecked").lower() == "true"
if text_setting("CompileOutputFolderOption") == "WorkFolder":
    compile_output_dir = text_setting("CompileOutputFullPath")
else:
    compile_output_dir = None


def element_to_dict(element):
    return {e.tag: e.text for e in element}


def apply_macros(path):
    if not path:
        return path
    for search, replace in library_path_macros.items():
        path = path.replace(search, replace)
    return path


def get_game_setup(game_name=DEFAULT_GAME):
    if game_name is DEFAULT_GAME:
        setup_element = game_setups[default_game_index]
    else:
        setup_element = next(e for e in game_setups if e.find("GameName").text == game_name)
    if not setup_element:
        raise KeyError('Couldn\'t find settings for "{}"'.format(game_name))
    return {e.tag: apply_macros(e.text) for e in setup_element}
