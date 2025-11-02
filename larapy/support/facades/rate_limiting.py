from larapy.support.facades.facade import Facade


class RateLimiting(Facade):

    @staticmethod
    def get_facade_accessor():
        return "rate_limiter"
