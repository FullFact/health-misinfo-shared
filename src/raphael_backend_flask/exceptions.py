class FlashException(Exception):
    def __init__(self, message: str, category: str = "danger") -> None:
        self.message = message
        self.category = category
