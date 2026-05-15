class ValidationError(Exception):
    """Erreur de validation affichable par un formulaire Forge."""

    def __init__(self, message: str | list[str]):
        if isinstance(message, list):
            self.messages = [str(item) for item in message]
        else:
            self.messages = [str(message)]
        super().__init__("; ".join(self.messages))
