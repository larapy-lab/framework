from larapy.support.service_provider import ServiceProvider
from larapy.database.seeding.seeder_runner import SeederRunner


class SeederServiceProvider(ServiceProvider):

    def register(self):
        self.container.singleton(
            "seeder.runner",
            lambda app: SeederRunner(
                app.make("db").connection(),
                app.make("config").get("database.seeders.paths", ["database/seeders"]),
            ),
        )
