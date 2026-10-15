"""Shared rules for create/update payloads, without changing response models."""
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator


class InputModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    non_nullable_fields: ClassVar[frozenset[str]] = frozenset()
    non_empty_fields: ClassVar[frozenset[str]] = frozenset({
        "student_code", "teacher_code", "class_code",
        "first_name", "last_name", "class_name",
    })

    @field_validator("*", mode="before")
    @classmethod
    def validate_supplied_value(cls, value, info: ValidationInfo):
        # Validators run on supplied fields, not omitted defaults. Updates may
        # omit required database columns, but must not explicitly clear them.
        if value is None and info.field_name in cls.non_nullable_fields:
            raise ValueError("Trường này không được nhận giá trị null")
        if isinstance(value, str) and info.field_name in cls.non_empty_fields:
            value = value.strip()
            if not value:
                raise ValueError("Trường này không được để trống")
            if len(value) > 255:
                raise ValueError("Trường này không được vượt quá 255 ký tự")
        return value
