import sys
from larapy.console.kernel import Kernel
from larapy.console.commands import (
    MigrateCommand,
    MigrateRollbackCommand,
    MigrateResetCommand,
    MigrateRefreshCommand,
    MigrateFreshCommand,
    MigrateStatusCommand,
    DbSeedCommand,
    MakeMigrationCommand,
    MakeSeederCommand,
    MakeFactoryCommand,
)
from larapy.console.commands.schedule_run import ScheduleRunCommand
from larapy.console.commands.schedule_list import ScheduleListCommand
from larapy.database.connection import Connection


def create_application(config: dict = None):
    if config is None:
        try:
            from config.database import database as db_config

            config = db_config
        except ImportError:
            config = {}

    connection = None
    if config:
        default_connection = config.get("default", "sqlite")
        connection_config = config.get("connections", {}).get(default_connection, {})

        if connection_config:
            connection = Connection(connection_config)
            connection.connect()

    kernel = Kernel()

    kernel.register_many(
        [
            lambda: MigrateCommand(connection, config),
            lambda: MigrateRollbackCommand(connection, config),
            lambda: MigrateResetCommand(connection, config),
            lambda: MigrateRefreshCommand(connection, config),
            lambda: MigrateFreshCommand(connection, config),
            lambda: MigrateStatusCommand(connection, config),
            lambda: DbSeedCommand(connection, config),
            lambda: MakeMigrationCommand(config),
            lambda: MakeSeederCommand(config),
            lambda: MakeFactoryCommand(config),
            lambda: ScheduleRunCommand(kernel),
            lambda: ScheduleListCommand(kernel),
        ]
    )

    return kernel


def main():
    kernel = create_application()
    exit_code = kernel.run(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
