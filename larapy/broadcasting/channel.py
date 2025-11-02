class Channel:
    def __init__(self, name: str):
        self.name = name

    def is_private(self) -> bool:
        return self.name.startswith("private-")

    def is_presence(self) -> bool:
        return self.name.startswith("presence-")

    def is_public(self) -> bool:
        return not self.is_private() and not self.is_presence()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Channel('{self.name}')"
