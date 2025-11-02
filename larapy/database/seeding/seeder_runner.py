import os
import importlib.util
from typing import List, Type, Union


class SeederRunner:

    def __init__(self, connection, seeder_paths: List[str] = None):
        self._connection = connection
        self._seeder_paths = seeder_paths or []
        self._called_seeders = []

    def call(self, seeder: Union[str, Type], silent: bool = False):
        if isinstance(seeder, str):
            seeder_instance = self._resolve(seeder)
        else:
            seeder_instance = seeder(self._connection)

        seeder_name = seeder_instance.__class__.__name__

        if not silent:
            print(f"Seeding: {seeder_name}")

        seeder_instance.run()

        self._called_seeders.append(seeder_name)

        if not silent:
            print(f"Seeded: {seeder_name}")

    def run(self, seeders: List[Union[str, Type]] = None):
        if seeders is None:
            seeders = self._discover_seeders()

        for seeder in seeders:
            self.call(seeder)

    def _discover_seeders(self) -> List[str]:
        seeders = []

        for path in self._seeder_paths:
            if not os.path.exists(path):
                continue

            for file in sorted(os.listdir(path)):
                if file.endswith(".py") and not file.startswith("__"):
                    seeders.append(file[:-3])

        return seeders

    def _resolve(self, seeder_name: str):
        for path in self._seeder_paths:
            file_path = os.path.join(path, f"{seeder_name}.py")

            if os.path.exists(file_path):
                spec = importlib.util.spec_from_file_location(seeder_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, seeder_name):
                    seeder_class = getattr(module, seeder_name)
                    if isinstance(seeder_class, type) and hasattr(seeder_class, "run"):
                        return seeder_class(self._connection)

                for attr_name in dir(module):
                    if attr_name == seeder_name:
                        continue

                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and hasattr(attr, "run"):
                        if attr_name != "Seeder" and attr_name.endswith("Seeder"):
                            return attr(self._connection)

        raise Exception(f"Seeder not found: {seeder_name}")

    def get_called_seeders(self) -> List[str]:
        return self._called_seeders
