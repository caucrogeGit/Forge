import copy
import datetime
import html
import re
from decimal import Decimal, InvalidOperation

from core.forms.exceptions import ValidationError
from core.http.slug import is_valid_slug

# FILES-VALIDATORS-KEEP-001 (ADR-019) : la validation de fichier (pure) reste
# dans le core mais hors de core/uploads/ (qui part vers forge-mvc-files).
from core.forms.upload_exceptions import UploadError
from core.forms.upload_validation import (
    validate_extension,
    validate_mime_type,
    validate_size,
)


EMPTY_VALUES = (None, "")


class Field:
    """Champ de formulaire Forge : lecture, conversion et validation locale."""

    def __init__(self, *, label: str | None = None, required: bool = True,
                 default=None, validators=None):
        self.name = ""
        self.label = label
        self.required = required
        self.default = default
        self.validators = list(validators or [])

    def clone(self):
        cloned = copy.copy(self)
        cloned.validators = list(self.validators)
        return cloned

    @property
    def display_label(self) -> str:
        return self.label or self.name.replace("_", " ").capitalize()

    def clean(self, raw_value, *, form=None):
        value = self._first(raw_value)
        if self._is_empty(value):
            if self.required:
                raise ValidationError(f"Le champ {self.display_label} est obligatoire.")
            return self.default

        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value

    def to_python(self, value):
        return value

    def validate(self, value) -> None:
        return None

    def run_validators(self, value) -> None:
        for validator in self.validators:
            result = validator(value)
            if isinstance(result, str) and result:
                raise ValidationError(result)
            if isinstance(result, list) and result:
                raise ValidationError(result)

    @staticmethod
    def _first(value):
        if isinstance(value, list):
            return value[0] if value else None
        return value

    @staticmethod
    def _is_empty(value) -> bool:
        return value in EMPTY_VALUES


class StringField(Field):
    def __init__(self, *, min_length: int | None = None, max_length: int | None = None,
                 pattern: str | None = None, strip: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.strip = strip

    def to_python(self, value) -> str:
        value = str(value)
        return value.strip() if self.strip else value

    def validate(self, value) -> None:
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                f"Le champ {self.display_label} doit contenir au moins {self.min_length} caracteres."
            )
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                f"Le champ {self.display_label} ne doit pas depasser {self.max_length} caracteres."
            )
        if self.pattern is not None and not self.pattern.fullmatch(value):
            raise ValidationError(f"Le champ {self.display_label} est invalide.")


class IntegerField(Field):
    def __init__(self, *, min_value: int | None = None, max_value: int | None = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def to_python(self, value) -> int:
        try:
            return int(str(value))
        except (TypeError, ValueError):
            raise ValidationError(f"Le champ {self.display_label} doit etre un entier.")

    def validate(self, value) -> None:
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"Le champ {self.display_label} doit etre superieur ou egal a {self.min_value}."
            )
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"Le champ {self.display_label} doit etre inferieur ou egal a {self.max_value}."
            )


class DecimalField(Field):
    def __init__(self, *, min_value: Decimal | int | str | None = None,
                 max_value: Decimal | int | str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = Decimal(str(min_value)) if min_value is not None else None
        self.max_value = Decimal(str(max_value)) if max_value is not None else None

    def to_python(self, value) -> Decimal:
        try:
            return Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            raise ValidationError(f"Le champ {self.display_label} doit etre un nombre.")

    def validate(self, value) -> None:
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"Le champ {self.display_label} doit etre superieur ou egal a {self.min_value}."
            )
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"Le champ {self.display_label} doit etre inferieur ou egal a {self.max_value}."
            )


class BooleanField(Field):
    TRUE_VALUES = {"1", "true", "on", "yes", "oui"}
    FALSE_VALUES = {"0", "false", "off", "no", "non"}

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("default", False)
        super().__init__(**kwargs)

    def to_python(self, value) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in self.TRUE_VALUES:
            return True
        if normalized in self.FALSE_VALUES:
            return False
        raise ValidationError(f"Le champ {self.display_label} doit etre un booleen.")


class ChoiceField(Field):
    """
    Champ de choix explicite.

    Les choix autorises sont fournis au champ ou au formulaire. Le champ ne va
    jamais les chercher lui-meme.
    """

    def __init__(self, *, choices=None, choices_key: str | None = None,
                 coerce=None, empty_value=None, **kwargs):
        super().__init__(**kwargs)
        self.choices = choices
        self.choices_key = choices_key
        self.coerce = coerce
        self.empty_value = empty_value

    def clean(self, raw_value, *, form=None):
        value = self._first(raw_value)
        if self._is_empty(value):
            if self.required:
                raise ValidationError(f"Le champ {self.display_label} est obligatoire.")
            return self.empty_value

        choices = self._resolve_choices(form)
        allowed_values = self._choice_values(choices) if choices is not None else None
        converted = self._coerce_value(value, allowed_values)

        if allowed_values is not None and converted not in set(allowed_values):
            raise ValidationError(f"Le champ {self.display_label} contient un choix invalide.")

        self.run_validators(converted)
        return converted

    def _coerce_value(self, value, allowed_values):
        coerce = self.coerce or self._infer_coerce(allowed_values)
        if coerce is None:
            return value
        if coerce is int and isinstance(value, bool):
            raise ValidationError(f"Le champ {self.display_label} contient un choix invalide.")
        try:
            return coerce(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Le champ {self.display_label} contient un choix invalide.")

    @staticmethod
    def _infer_coerce(allowed_values):
        if not allowed_values:
            return None
        first = next(iter(allowed_values))
        if isinstance(first, bool):
            return None
        if isinstance(first, int):
            return int
        return type(first)

    def _resolve_choices(self, form):
        source = self.choices
        if isinstance(source, str):
            return self._option(form, source, required=True)
        if source is not None:
            return source() if callable(source) else source

        if self.choices_key:
            return self._option(form, self.choices_key, required=True)

        if self.name:
            found = self._option(form, f"allowed_{self.name}", required=False)
            if found is not None:
                return found
        return None

    @staticmethod
    def _choice_values(choices) -> list:
        if isinstance(choices, dict):
            return list(choices.keys())
        values = []
        for item in choices:
            if isinstance(item, tuple | list) and item:
                values.append(item[0])
            else:
                values.append(item)
        return values

    def _option(self, form, name: str, *, required: bool):
        if form is not None and name in form.options:
            value = form.options[name]
            return value() if callable(value) else value
        if required:
            raise ValidationError(
                f"La liste de choix pour le champ {self.display_label} est absente."
            )
        return None


class RelatedIdsField(Field):
    """
    Liste d'identifiants lies, utile pour les formulaires de pivot explicite.

    Ne charge jamais les valeurs autorisees lui-meme : elles sont fournies par
    le formulaire via options, ou directement au constructeur.
    """

    def __init__(self, *, allowed_ids=None, allowed_ids_key: str | None = None, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)
        self.allowed_ids = allowed_ids
        self.allowed_ids_key = allowed_ids_key

    def clean(self, raw_value, *, form=None):
        values = self._values(raw_value)
        if not values:
            if self.required:
                raise ValidationError(f"Le champ {self.display_label} est obligatoire.")
            return []

        ids = self._to_unique_ints(values)
        allowed_ids = self._resolve_allowed_ids(form)
        if allowed_ids is not None:
            allowed = set(allowed_ids)
            invalid = [value for value in ids if value not in allowed]
            if invalid:
                details = ", ".join(str(value) for value in invalid)
                raise ValidationError(
                    f"Le champ {self.display_label} contient des identifiants non autorises : {details}."
                )

        self.run_validators(ids)
        return ids

    def _values(self, raw_value) -> list:
        if raw_value is None:
            return []
        if isinstance(raw_value, list):
            values = raw_value
        elif isinstance(raw_value, tuple | set):
            values = list(raw_value)
        else:
            values = [raw_value]
        return [value for value in values if value not in EMPTY_VALUES]

    def _to_unique_ints(self, values) -> list[int]:
        result = []
        seen = set()
        for value in values:
            if isinstance(value, bool):
                raise ValidationError(f"Le champ {self.display_label} doit contenir des entiers.")
            try:
                identifier = int(str(value))
            except (TypeError, ValueError):
                raise ValidationError(f"Le champ {self.display_label} doit contenir des entiers.")
            if identifier not in seen:
                seen.add(identifier)
                result.append(identifier)
        return result

    def _resolve_allowed_ids(self, form):
        source = self.allowed_ids
        if isinstance(source, str):
            return self._option(form, source, required=True)
        if source is not None:
            return source() if callable(source) else source

        if self.allowed_ids_key:
            return self._option(form, self.allowed_ids_key, required=True)

        if self.name:
            option_name = f"allowed_{self.name}"
            found = self._option(form, option_name, required=False)
            if found is not None:
                return found
        return None

    def _option(self, form, name: str, *, required: bool):
        if form is not None and name in form.options:
            value = form.options[name]
            return value() if callable(value) else value
        if required:
            raise ValidationError(
                f"La liste autorisee pour le champ {self.display_label} est absente."
            )
        return None


_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


class EmailField(StringField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 254)
        super().__init__(**kwargs)

    def validate(self, value: str) -> None:
        super().validate(value)
        if not _EMAIL_RE.fullmatch(value):
            raise ValidationError(
                f"Le champ {self.display_label} doit etre une adresse email valide."
            )


_PHONE_RE = re.compile(r'^(?:\+33[\s.]?|0)[0-9](?:[\s.\-]?[0-9]{2}){4}$')


class PhoneField(StringField):
    def validate(self, value: str) -> None:
        super().validate(value)
        if not _PHONE_RE.fullmatch(value):
            raise ValidationError(
                f"Le champ {self.display_label} doit etre un numero de telephone valide."
            )


_URL_RE = re.compile(r'^https?://\S+\.\S+$', re.IGNORECASE)


class UrlField(StringField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 2048)
        super().__init__(**kwargs)

    def validate(self, value: str) -> None:
        super().validate(value)
        if not _URL_RE.fullmatch(value):
            raise ValidationError(
                f"Le champ {self.display_label} doit etre une URL valide (http:// ou https://)."
            )


class TextAreaField(StringField):
    def __init__(self, *, rows: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self.rows = rows

    def render(self, value: str = "") -> str:
        attrs = [f'name="{html.escape(self.name)}"']
        if self.rows is not None:
            attrs.append(f'rows="{self.rows}"')
        if self.required:
            attrs.append("required")
        if self.min_length is not None:
            attrs.append(f'minlength="{self.min_length}"')
        if self.max_length is not None:
            attrs.append(f'maxlength="{self.max_length}"')
        return f'<textarea {" ".join(attrs)}>{html.escape(str(value))}</textarea>'


_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class DateField(Field):
    def to_python(self, value) -> datetime.date:
        s = str(value).strip()
        if not _DATE_RE.fullmatch(s):
            raise ValidationError(
                f"Le champ {self.display_label} doit etre une date valide au format YYYY-MM-DD."
            )
        try:
            return datetime.date.fromisoformat(s)
        except ValueError:
            raise ValidationError(
                f"Le champ {self.display_label} doit etre une date valide au format YYYY-MM-DD."
            )


_DATETIME_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?$')
_DATETIME_FMTS = ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M")


class DateTimeField(Field):
    def to_python(self, value) -> datetime.datetime:
        s = str(value).strip()
        if not _DATETIME_RE.fullmatch(s):
            raise ValidationError(
                f"Le champ {self.display_label} doit etre une date/heure valide au format YYYY-MM-DDTHH:MM."
            )
        for fmt in _DATETIME_FMTS:
            try:
                return datetime.datetime.strptime(s, fmt)
            except ValueError:
                continue
        raise ValidationError(
            f"Le champ {self.display_label} doit etre une date/heure valide au format YYYY-MM-DDTHH:MM."
        )


class RelationField(ChoiceField):
    """Champ de relation many_to_one — clé étrangère validée par liste de choix."""

    def __init__(self, *, target: str = "", target_label_field: str = "", **kwargs):
        super().__init__(**kwargs)
        self.target = target
        self.target_label_field = target_label_field


class SlugField(StringField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 120)
        super().__init__(**kwargs)

    def validate(self, value: str) -> None:
        # Vide / longueur / min sont gérés par StringField.validate ;
        # le format URL-slug est délégué au module canonique (ADR-017, §11).
        super().validate(value)
        if not is_valid_slug(value, max_length=self.max_length):
            raise ValidationError(
                f"Le champ {self.display_label} doit contenir uniquement des lettres"
                " minuscules, des chiffres et des tirets, sans tiret au debut ou a la fin."
            )


class FileField(Field):
    def __init__(self, *,
                 allowed_extensions=None,
                 max_size: int | None = None,
                 allowed_mime_types=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.allowed_extensions = allowed_extensions
        self.max_size = max_size
        self.allowed_mime_types = allowed_mime_types

    @staticmethod
    def _is_empty(value) -> bool:
        if value is None or value == "":
            return True
        filename = getattr(value, "filename", None)
        if not filename or not str(filename).strip():
            return True
        size = getattr(value, "size", None)
        return size is not None and size == 0

    def to_python(self, value):
        return value

    def validate(self, value) -> None:
        filename = getattr(value, "filename", "")
        size = getattr(value, "size", 0)
        mime_type = getattr(value, "content_type", None)

        if self.allowed_extensions is not None:
            try:
                validate_extension(filename, self.allowed_extensions)
            except UploadError as exc:
                raise ValidationError(
                    f"Le champ {self.display_label} : {exc}"
                ) from exc

        if self.max_size is not None:
            try:
                validate_size(size, self.max_size)
            except UploadError as exc:
                raise ValidationError(
                    f"Le champ {self.display_label} : {exc}"
                ) from exc

        if self.allowed_mime_types is not None:
            try:
                validate_mime_type(mime_type, self.allowed_mime_types)
            except UploadError as exc:
                raise ValidationError(
                    f"Le champ {self.display_label} : {exc}"
                ) from exc


_IMAGE_DEFAULT_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
_IMAGE_DEFAULT_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]


class ImageField(FileField):
    def __init__(self, *,
                 allowed_extensions=None,
                 allowed_mime_types=None,
                 **kwargs):
        super().__init__(
            allowed_extensions=(
                allowed_extensions if allowed_extensions is not None
                else _IMAGE_DEFAULT_EXTENSIONS
            ),
            allowed_mime_types=(
                allowed_mime_types if allowed_mime_types is not None
                else _IMAGE_DEFAULT_MIME_TYPES
            ),
            **kwargs,
        )
