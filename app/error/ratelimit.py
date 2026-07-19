"""Rate-limiting exception, raised by `app.middleware.ratelimiting_middleware`."""


class RateLimit(Exception):
    def __init__(self, message: str, headers: dict, error_code: str = "rate_limit"):
        self.message = message
        self.error_code = error_code
        self.headers = headers
        super().__init__(self.message)
