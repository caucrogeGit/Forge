"""FICHIER GENERE PAR FORGE.
Base regenerable de l'entite Media.
Ne pas y ajouter de logique metier manuelle.
"""

from __future__ import annotations

from datetime import datetime

from core.validation import (
    ValidationError,
    min_value,
    nullable,
    typed,
)


class MediaBase:
    """Classe de base regenerable de Media."""

    def __init__(self, entity_name, entity_id, path, original_name, mime_type, size, created_at, id=None, role='default', position=0, alt_text=None):
        self.entity_name = entity_name
        self.entity_id = entity_id
        self.path = path
        self.original_name = original_name
        self.mime_type = mime_type
        self.size = size
        self.created_at = created_at
        self.id = id
        self.role = role
        self.position = position
        self.alt_text = alt_text

    @staticmethod
    def _coerce_datetime(value):
        if value is None or isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)

    @property
    def id(self):
        return self._id

    @id.setter
    @typed(int)
    @nullable
    def id(self, value):
        if value is None:
            self._id = None
            return
        self._id = value

    @property
    def entity_name(self):
        return self._entity_name

    @entity_name.setter
    @typed(str)
    def entity_name(self, value):
        if value is None:
            raise ValidationError("entity_name", 'La propriété "entity_name" ne peut pas être nulle.')
        self._entity_name = value

    @property
    def entity_id(self):
        return self._entity_id

    @entity_id.setter
    @typed(int)
    @min_value(1)
    def entity_id(self, value):
        if value is None:
            raise ValidationError("entity_id", 'La propriété "entity_id" ne peut pas être nulle.')
        self._entity_id = value

    @property
    def path(self):
        return self._path

    @path.setter
    @typed(str)
    def path(self, value):
        if value is None:
            raise ValidationError("path", 'La propriété "path" ne peut pas être nulle.')
        self._path = value

    @property
    def original_name(self):
        return self._original_name

    @original_name.setter
    @typed(str)
    def original_name(self, value):
        if value is None:
            raise ValidationError("original_name", 'La propriété "original_name" ne peut pas être nulle.')
        self._original_name = value

    @property
    def mime_type(self):
        return self._mime_type

    @mime_type.setter
    @typed(str)
    def mime_type(self, value):
        if value is None:
            raise ValidationError("mime_type", 'La propriété "mime_type" ne peut pas être nulle.')
        self._mime_type = value

    @property
    def size(self):
        return self._size

    @size.setter
    @typed(int)
    @min_value(0)
    def size(self, value):
        if value is None:
            raise ValidationError("size", 'La propriété "size" ne peut pas être nulle.')
        self._size = value

    @property
    def role(self):
        return self._role

    @role.setter
    @typed(str)
    def role(self, value):
        if value is None:
            raise ValidationError("role", 'La propriété "role" ne peut pas être nulle.')
        self._role = value

    @property
    def position(self):
        return self._position

    @position.setter
    @typed(int)
    @min_value(0)
    def position(self, value):
        if value is None:
            raise ValidationError("position", 'La propriété "position" ne peut pas être nulle.')
        self._position = value

    @property
    def alt_text(self):
        return self._alt_text

    @alt_text.setter
    @typed(str)
    @nullable
    def alt_text(self, value):
        if value is None:
            self._alt_text = None
            return
        self._alt_text = value

    @property
    def created_at(self):
        return self._created_at

    @created_at.setter
    @typed(datetime)
    def created_at(self, value):
        if value is None:
            raise ValidationError("created_at", 'La propriété "created_at" ne peut pas être nulle.')
        self._created_at = value

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity_name": self.entity_name,
            "entity_id": self.entity_id,
            "path": self.path,
            "original_name": self.original_name,
            "mime_type": self.mime_type,
            "size": self.size,
            "role": self.role,
            "position": self.position,
            "alt_text": self.alt_text,
            "created_at": None if self.created_at is None else self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MediaBase":
        return cls(
            id=data.get("id"),
            entity_name=data.get("entity_name"),
            entity_id=data.get("entity_id"),
            path=data.get("path"),
            original_name=data.get("original_name"),
            mime_type=data.get("mime_type"),
            size=data.get("size"),
            role=data.get("role"),
            position=data.get("position"),
            alt_text=data.get("alt_text"),
            created_at=cls._coerce_datetime(data.get("created_at")),
        )

    def __repr__(self) -> str:
        return f"MediaBase(id={self.id!r}, entity_name={self.entity_name!r}, entity_id={self.entity_id!r}, path={self.path!r}, original_name={self.original_name!r}, mime_type={self.mime_type!r}, size={self.size!r}, role={self.role!r}, position={self.position!r}, alt_text={self.alt_text!r}, created_at={self.created_at!r})"

