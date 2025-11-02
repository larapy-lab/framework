from larapy.support.service_provider import ServiceProvider
from larapy.translation.file_loader import FileLoader
from larapy.translation.translator import Translator
from larapy.translation import helpers
import os


class TranslationServiceProvider(ServiceProvider):

    def register(self):
        self.register_loader()
        self.register_translator()

    def register_loader(self):
        def loader_factory(app):
            paths = []

            lang_path = app.base_path("lang")
            if os.path.exists(lang_path):
                paths.append(lang_path)

            resources_lang_path = app.base_path("resources/lang")
            if os.path.exists(resources_lang_path):
                paths.append(resources_lang_path)

            if not paths:
                paths = [app.base_path("lang")]

            return FileLoader(paths)

        self.app.singleton("translation.loader", loader_factory)

    def register_translator(self):
        def translator_factory(app):
            loader = app.make("translation.loader")

            locale = "en"
            if hasattr(app, "config"):
                config = app.make("config")
                locale = config.get("app.locale", "en")

            translator = Translator(loader, locale)

            fallback = "en"
            if hasattr(app, "config"):
                config = app.make("config")
                fallback = config.get("app.fallback_locale", "en")

            translator.set_fallback(fallback)

            helpers.set_translator(translator)

            return translator

        self.app.singleton("translator", translator_factory)

    def boot(self):
        pass
