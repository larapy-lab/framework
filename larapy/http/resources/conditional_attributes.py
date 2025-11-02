class ConditionalValue:
    def __init__(self, condition, value, default=None):
        self.condition = condition
        self.value = value
        self.default = default

    def resolve(self):
        if callable(self.condition):
            condition = self.condition()
        else:
            condition = self.condition

        if condition:
            return self.value() if callable(self.value) else self.value

        if self.default is None:
            return MissingValue()

        return self.default() if callable(self.default) else self.default


class MergeValue:
    def __init__(self, data: dict):
        self.data = data

    def resolve(self):
        return self.data


class MissingValue:
    def __repr__(self):
        return "<MissingValue>"

    def __bool__(self):
        return False
