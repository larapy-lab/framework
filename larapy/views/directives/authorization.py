def can_directive(arguments: str) -> str:
    """
    @can directive for templates.
    Usage: @can('update', post)
    """
    parts = [p.strip() for p in arguments.split(",", 1)]
    ability = parts[0].strip("\"'")
    model = parts[1].strip() if len(parts) > 1 else "None"

    return f"{{% if gate.allows('{ability}', {model}) %}}"


def endcan_directive(arguments: str = "") -> str:
    """@endcan directive for templates."""
    return "{% endif %}"


def cannot_directive(arguments: str) -> str:
    """
    @cannot directive for templates.
    Usage: @cannot('delete', post)
    """
    parts = [p.strip() for p in arguments.split(",", 1)]
    ability = parts[0].strip("\"'")
    model = parts[1].strip() if len(parts) > 1 else "None"

    return f"{{% if gate.denies('{ability}', {model}) %}}"


def endcannot_directive(arguments: str = "") -> str:
    """@endcannot directive for templates."""
    return "{% endif %}"


def canany_directive(arguments: str) -> str:
    """
    @canany directive for templates.
    Usage: @canany(['update', 'delete'], post)
    """
    parts = [p.strip() for p in arguments.split(",", 1)]
    abilities = parts[0].strip()
    model = parts[1].strip() if len(parts) > 1 else "None"

    return f"{{% if gate.any({abilities}, {model}) %}}"


def endcanany_directive(arguments: str = "") -> str:
    """@endcanany directive for templates."""
    return "{% endif %}"
