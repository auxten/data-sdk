from dataclasses import dataclass, field
from typing import Any, Type, List, Optional, ClassVar
import datetime


class Field:
    def __init__(
        self,
        primary_key: bool = False,
        auto_uuid: bool = False,
        default_now: bool = False,
        default: Any = None,
    ):
        self.primary_key = primary_key
        self.auto_uuid = auto_uuid
        self.default_now = default_now
        self.default = default


class VectorIndex:
    def __init__(
        self,
        name: str,
        source_field: str,
        model: str,
        dim: int,
        distance_function: str = "cosineDistance",
    ):
        self.name = name
        self.source_field = source_field
        self.model = model
        self.dim = dim
        self.distance_function = distance_function
        self.embedding_column = f"{source_field}_embedding"


class Meta:
    engine: str = "MergeTree"
    order_by: tuple = ("id",)
    indexes: List[VectorIndex] = []


class Table:
    Meta: ClassVar[Meta] = Meta()

    @classmethod
    def get_schema(cls) -> str:
        """Generate SQL schema from dataclass fields"""
        fields = []
        primary_key_fields = []

        for name, field in cls.__dataclass_fields__.items():
            field_type = field.type
            field_def = field.default

            # Map Python types to ClickHouse types
            type_mapping = {
                str: "String",
                int: "Int64",
                float: "Float64",
                bool: "Bool",
                datetime.datetime: "DateTime",
            }

            ch_type = type_mapping.get(field_type, "String")

            # Handle special field attributes
            if isinstance(field_def, Field):
                if field_def.primary_key:
                    primary_key_fields.append(name)
                if field_def.auto_uuid:
                    ch_type = f"{ch_type} DEFAULT generateUUIDv4()"
                if field_def.default_now:
                    ch_type = f"{ch_type} DEFAULT now()"
                if field_def.default is not None:
                    ch_type = f"{ch_type} DEFAULT {field_def.default}"

            fields.append(f"{name} {ch_type}")

        # Add PRIMARY KEY clause if there are primary key fields
        if primary_key_fields:
            fields.append(f"PRIMARY KEY ({', '.join(primary_key_fields)})")

        return ",\n    ".join(fields)

    @classmethod
    def get_indexes(cls) -> List[VectorIndex]:
        """Get all vector indexes defined in the Meta class"""
        return cls.Meta.indexes if hasattr(cls.Meta, "indexes") else []

    def to_dict(self) -> dict:
        """Convert the dataclass instance to a dictionary"""
        return {field: getattr(self, field) for field in self.__dataclass_fields__}
