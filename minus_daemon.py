import argparse, os, time
from typing import Callable
from . import crowbar_settings, compile_model


class FileWatcher:
    def __init__(self, directory: str, callback_function: Callable, interval: float=1.):
        self.directory = directory
        self.callback_function = callback_function
        self.interval = interval
        self.file_modification_times = {}

    def start(self):
        while True:
            files = os.listdir(self.directory)

            for file in files:
                file_path = os.path.join(self.directory, file)
                last_modification_time = os.path.getmtime(file_path)

                if file_path not in self.file_modification_times:
                    print("Adding", file_path)
                    self.file_modification_times[file_path] = last_modification_time
                    self.callback_function(file_path)
                elif last_modification_time > self.file_modification_times[file_path]:
                    print("Updating", file_path)
                    self.file_modification_times[file_path] = last_modification_time
                    self.callback_function(file_path)

            time.sleep(self.interval)


def main(path, game, addon_path=None):
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
    args = parser.parse_args()

    main(args.path, args.game, args.addon_path)
