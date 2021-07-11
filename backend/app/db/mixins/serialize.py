from typing import Any
from collections.abc import Iterable

from .inspection import InspectionMixin


class SerializeMixin(InspectionMixin):
    """Mixin to make model serializable."""

    __abstract__ = True

    def as_dict(
        self,
        nested: bool = False,
        hybrid_attributes: bool = False,
        exclude: list[str] = None,
    ) -> dict[str, Any]:
        """Return dict object with model's data.

        Args:
            nested (bool, optional): flag to return nested relationships' data if true.
                                     Defaults to False.
            hybrid_attributes (bool, optional): flag to include hybrid attributes
                                                if true. Defaults to False.
            exclude (list[str], optional): list of exclude fields. Defaults to None.

        """
        result = {}

        if exclude is None:
            view_cols = self.columns
        else:
            view_cols = filter(lambda e: e not in exclude, self.columns)

        for key in view_cols:
            result[key] = getattr(self, key)

        if hybrid_attributes:
            for key in self.hybrid_properties:
                result[key] = getattr(self, key)

        if nested:
            for key in self.relations:
                if exclude and key in exclude:
                    continue

                obj = getattr(self, key)

                if isinstance(obj, SerializeMixin):
                    result[key] = obj.as_dict(hybrid_attributes=hybrid_attributes)
                elif isinstance(obj, Iterable):
                    result[key] = [
                        o.as_dict(hybrid_attributes=hybrid_attributes, nested=False)
                        for o in obj
                        if isinstance(o, SerializeMixin)
                    ]

        return result
