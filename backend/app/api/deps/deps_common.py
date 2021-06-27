from typing import Optional


class CommonQueryParams:
    def __init__(self, q: Optional[str] = None, skip: int = 0, limit: int = 20):
        self.q = q
        self.skip = skip
        self.limit = limit
