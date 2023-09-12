import argparse, os, subprocess, time
from typing import Callable
from . import crowbar_settings, compile_model


class FileWatcher:
    def __init__(self, directory: str, callback_function: Callable, interval: float = 1.0):
        self.directory = directory
        self.callback_function = callback_function
        self.interval = interval
        self.file_modification_times = {}

        files = os.listdir(self.directory)
        for file in files:
            file_path = os.path.join(self.directory, file)
            self.file_modification_times[file_path] = os.path.getmtime(file_path)

    def on_modified(self, file_path, mtime):
        self.file_modification_times[file_path] = mtime
        self.callback_function(file_path)

    def start(self):
        while True:
            files = os.listdir(self.directory)

            for file in files:
                file_path = os.path.join(self.directory, file)
                mtime = os.path.getmtime(file_path)

                if file_path not in self.file_modification_times:
                    print("Adding", file_path)
                    self.on_modified(file_path, mtime)
                elif mtime > self.file_modification_times[file_path]:
                    print("Updating", file_path)
                    self.on_modified(file_path, mtime)

            time.sleep(self.interval)


def main(path, game, addon_path=None, start_mapping_tool=True):
    if start_mapping_tool:
        game_setup = crowbar_settings.get_game_setup(game)
        subprocess.Popen([game_setup["MappingToolPathFileName"]], close_fds=True)

    def on_new_file(file_path):
        if os.path.splitext(file_path)[-1] == ".dmx":
            compile_model.main(file_path, game, addon_path, do_convert_materials=True)

    boy_watcher = FileWatcher(path, on_new_file)
    boy_watcher.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=os.getcwd())
    parser.add_argument("--game", default=crowbar_settings.DEFAULT_GAME)
    parser.add_argument("--addon-path", default=crowbar_settings.compile_output_dir)
    parser.add_argument("--start-mapping-tool", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    main(args.path, args.game, args.addon_path, args.start_mapping_tool)
