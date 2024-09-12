class FlashException(Exception):
    def __init__(self, message: str, category: str = "danger") -> None:
        super().__init__(message)
        self.message = message
        self.category = category
