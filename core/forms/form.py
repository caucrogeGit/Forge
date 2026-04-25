from core.forms.exceptions import ValidationError
from core.forms.fields import Field


NON_FIELD_ERRORS = "__all__"


class FormMeta(type):
    """Collecte les Field declares sur la classe de formulaire."""

    def __new__(mcls, name, bases, attrs):
        declared = {}
        for base in bases:
            declared.update(getattr(base, "declared_fields", {}))

        for attr_name, value in list(attrs.items()):
            if isinstance(value, Field):
                value.name = attr_name
                declared[attr_name] = value
                attrs.pop(attr_name)

        attrs["declared_fields"] = declared
        return super().__new__(mcls, name, bases, attrs)


class Form(metaclass=FormMeta):
    """
    Formulaire Forge.

    Transforme une source HTTP en donnees validees et erreurs affichables.
    Ne connait ni la base de donnees, ni les redirections, ni la logique metier.
    """

    declared_fields: dict[str, Field] = {}

    def __init__(self, data=None, **options):
        self.raw_data = data or {}
        self.data = self._flatten(self.raw_data)
        self.options = dict(options)
        self.fields = self._clone_fields()
        self.cleaned_data = {}
        self._errors = {}
        self._is_bound = data is not None

    @classmethod
    def from_request(cls, request, **options):
        return cls(request.body, **options)

    @property
    def is_bound(self) -> bool:
        return self._is_bound

    @property
    def errors(self) -> dict[str, list[str]]:
        return {field: list(messages) for field, messages in self._errors.items()}

    @property
    def non_field_errors(self) -> list[str]:
        return list(self._errors.get(NON_FIELD_ERRORS, []))

    def field_errors(self, name: str) -> list[str]:
        return list(self._errors.get(name, []))

    def value(self, name: str, default=""):
        return self.data.get(name, default)

    def error(self, name: str, default="") -> str:
        errors = self.field_errors(name)
        return errors[0] if errors else default

    def has_error(self, name: str) -> bool:
        return bool(self._errors.get(name))

    def add_error(self, field: str | None, message: str | list[str]) -> None:
        key = field or NON_FIELD_ERRORS
        messages = message if isinstance(message, list) else [message]
        self._errors.setdefault(key, []).extend(str(item) for item in messages)

    def is_valid(self) -> bool:
        self.full_clean()
        return not self._errors

    def full_clean(self) -> None:
        self.cleaned_data = {}
        self._errors = {}

        for name, field in self.fields.items():
            try:
                self.cleaned_data[name] = field.clean(self.raw_data.get(name), form=self)
            except ValidationError as exc:
                self.add_error(name, exc.messages)

        if self._errors:
            return

        try:
            extra_data = self.clean()
        except ValidationError as exc:
            self.add_error(None, exc.messages)
            return

        if isinstance(extra_data, dict):
            self.cleaned_data.update(extra_data)

    def clean(self):
        """Point d'extension pour les validations entre champs."""
        return None

    @property
    def context(self) -> dict:
        return {
            "data": dict(self.data),
            "errors": self.errors,
            "cleaned_data": dict(self.cleaned_data),
        }

    @staticmethod
    def _flatten(data) -> dict:
        flattened = {}
        for key, value in data.items():
            if isinstance(value, list):
                flattened[key] = value if len(value) > 1 else value[0] if value else ""
            else:
                flattened[key] = value
        return flattened

    @classmethod
    def _clone_fields(cls) -> dict[str, Field]:
        fields = {}
        for name, field in cls.declared_fields.items():
            clone = field.clone()
            clone.name = name
            fields[name] = clone
        return fields
