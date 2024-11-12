import asyncio
import base64
import binascii
import copy
import dataclasses
import functools
import inspect
import pickle
import typing
from dataclasses import MISSING, Field, dataclass, field, fields
from enum import Enum
from typing import Any, Callable

from ..cell_api import CellApiMixin, CellEvent
from ..neptyne_protocol import MIMETypes
from ..util import list_like
from .color import Color
from .register_widget import (
    is_union_type,
    list_like_type,
    widget_class_by_name,
    widget_registry,
)

BUNDLE_TAG = "widget"
VALUE_ATTRIBUTE = "__value"
ACTION_ATTRIBUTE = "action"
VALUE_JSON_FIELD = "value"


class StrEnum(str, Enum):
    pass


def decode_callable(v: str) -> Callable | None:
    try:
        return pickle.loads(base64.b64decode(v.encode("utf-8")))
    except (pickle.PickleError, AttributeError, binascii.Error):
        return None


def encode_callable(value: Callable) -> str | None:
    try:
        return base64.b64encode(pickle.dumps(value)).decode("utf-8")
    except pickle.PickleError:
        return None


def widget_field(  # type: ignore
    description: str,
    default: Any = MISSING,
    category: str | None = None,
    default_factory: Callable = MISSING,  # type: ignore
    inline: bool = False,
):
    metadata = {"description": description, "category": category, "inline": inline}
    if default is not MISSING:
        if default_factory is not MISSING:
            raise ValueError("Cannot specify both default and default_factory")
        return field(
            metadata=metadata,
            default=default,
        )

    return field(
        metadata=metadata,
        default_factory=default_factory,
    )


def validate_non_union_type(value: typing.Any, t: type) -> bool:
    origin = typing.get_origin(t)
    if origin:
        return isinstance(value, origin) or (
            list_like(value) and list_like_type(origin)
        )
    else:
        return isinstance(value, t)


def validate_type(value: typing.Any, t: type) -> str | None:
    if is_union_type(t):
        for typ in typing.get_args(t):
            if validate_non_union_type(value, typ):
                return None
    else:
        if validate_non_union_type(value, t):
            return None

    return f"Value: {value}, is not instance of {t!r}"


def maybe_cast_non_union_primitive_type(value: Any, t: type) -> tuple[Any, bool]:
    if t is float and isinstance(value, int):
        return float(value), True

    if t is int and isinstance(value, float) and int(value) == value:
        return int(value), True

    if t is str:
        return repr(value), True

    if (
        inspect.isclass(t)
        and (issubclass(t, Color) or issubclass(t, Enum))
        and isinstance(value, str)
    ):
        return t(value), True

    return value, False


def maybe_cast_primitive_types(value: Any, t: type) -> Any:
    if is_union_type(t):
        for typ in typing.get_args(t):
            value, did_cast = maybe_cast_non_union_primitive_type(value, typ)
            if did_cast:
                break
    else:
        value, did_cast = maybe_cast_non_union_primitive_type(value, t)

    return value


def maybe_cast_to_list(value: Any) -> list:
    if hasattr(value, "to_list"):
        return value.to_list()
    return value


def required_parameter_error_message(name: str) -> str:
    return f"Required parameter {name} is unset"


def validate_widget_params(widget_name: str, params: dict[str, Any]) -> dict[str, str]:
    cls = widget_class_by_name.get(widget_name.lower())
    registry_info = widget_registry.widgets.get(widget_name)
    if cls is None or registry_info is None:
        raise ValueError(f"Unknown widget type: {widget_name}")
    errors: dict[str, str] = {}

    # Check for missing required params.
    for param in registry_info.params:
        if not param.optional:
            # TODO: Be more careful with this check after restricting required params
            if params.get(param.name) is None:
                errors[param.name] = required_parameter_error_message(param.name)

    # Check for invalid param types.
    for param_name, value in params.items():
        if param_name in errors:
            continue

        t = cls.get_annotations().get(param_name)
        if not validate_type(value, t):
            continue

        value = maybe_cast_primitive_types(value, t)

        if field_error := validate_type(value, t):
            errors[param_name] = field_error

    return errors


@dataclass
class BaseWidget(CellApiMixin):
    mime_type = MIMETypes.APPLICATION_VND_NEPTYNE_WIDGET_V1_JSON

    def maybe_validate_list(self, candidate: Any) -> str | None:
        from ..primitives import Empty

        if list_like(candidate):
            for item in candidate:
                if list_like(item):
                    if error := self.maybe_validate_list(item):
                        return error
                elif not isinstance(item, str | float | int | bool | None | Empty):
                    return "List elements must be simple values"

    def validate_all_fields(self) -> dict[str, str]:
        errors = {}
        for f in dataclasses.fields(self):
            v = getattr(self, f.name)
            if error := self.maybe_validate_list(v):
                errors[f.name] = error
                continue

            # Validate type. If it doesn't match any, attempt cast and revalidate.
            if not validate_type(v, f.type):
                continue

            v = maybe_cast_primitive_types(v, f.type)
            setattr(self, f.name, v)

            if field_error := validate_type(v, f.type):
                errors[f.name] = field_error

        if errors:
            return errors

        return self.validate_fields()

    # Per widget custom validation (e.g. in scatter len(x) == len(y))
    def validate_fields(self) -> dict[str, str]:
        return {}

    def get_arg(self, field: Field) -> Any:
        from ..cell_range import CellRange

        value = getattr(self, field.name)
        if callable(value):
            value = encode_callable(value)
        if isinstance(value, Color):
            value = value.webcolor
        if isinstance(value, CellRange):
            if value.two_dimensional:
                value = [[*row] for row in value]
            else:
                value = [*value]
        return value

    def _repr_mimebundle_(
        self, include: Any = False, exclude: Any = False, **kwargs: Any
    ) -> dict:
        payload = {f.name: self.get_arg(f) for f in fields(self)}
        if self._check_has_value():
            payload[VALUE_JSON_FIELD] = self.value
        payload[BUNDLE_TAG] = self.__class__.__name__.lower()
        data = {self.mime_type.value: payload}
        if include:
            data = {k: v for (k, v) in data.items() if k in include}
        if exclude:
            data = {k: v for (k, v) in data.items() if k not in exclude}
        return data

    def _check_has_value(self) -> bool:
        return hasattr(self, "default_value")

    def _check_valid_value(self, value: Any) -> bool:
        return True

    @property
    def value(self) -> Any:
        if not self._check_has_value():
            raise AttributeError("Widget has no value")
        return getattr(self, VALUE_ATTRIBUTE, self.default_value)  # type: ignore

    @value.setter
    def value(self, new_value: Any) -> None:
        self.set_value(new_value, do_trigger=True)

    def set_value(self, new_value: Any, *, do_trigger: bool) -> None:
        setattr(self, VALUE_ATTRIBUTE, new_value)
        if not self._check_has_value():
            raise AttributeError("Cannot set a value for widget")
        if not self._check_valid_value(new_value):
            raise ValueError(
                f"{new_value} is an invalid value for {self.__class__.__name__}"
            )
        if do_trigger:
            from ..dash_ref import DashRef

            assert isinstance(self.ref, DashRef)
            dash = self.ref.dash
            dash.evaluate_and_trigger_widget(self.ref.range.origin(), new_value, False)

    def __json__(self) -> dict:
        return self.__dict__

    def trigger(
        self, new_value: Any, event: CellEvent, do_copy_from_code: bool = True
    ) -> None:
        from ..dash_ref import DashRef

        assert isinstance(self.ref, DashRef)

        dash = self.ref.dash
        address = self.ref.range.origin()

        if do_copy_from_code:
            # Compute copy_from using kernel state
            copy_from = dash.init_widget_copy_from(address)

            if copy_from is not None:
                # Copy all callables from the copy_from so they are up to date. Use the __dict__ trick
                # to avoid triggering the setter.
                to_copy = {
                    f.name: getattr(copy_from, f.name)
                    for f in fields(copy_from)
                    if callable(getattr(copy_from, f.name))
                }
                self.__dict__.update(to_copy)

        if self._check_has_value():
            setattr(self, VALUE_ATTRIBUTE, new_value)
            dash.update_cell_meta_on_value_change(
                address, dash.cells[address.sheet].get(address)
            )
            dash.notify_client_cells_have_changed(self.ref.range.origin())
            dash.flush_side_effects(address.to_coord())

        if hasattr(self, ACTION_ATTRIBUTE) and self.action is not None:  # type: ignore
            if isinstance(self.action, str):  # type: ignore
                decoded = decode_callable(self.action)  # type: ignore
                if decoded:
                    self.action = decoded
            action = self.action
            # When we set a value during construction from json, action is not yet callable:
            if callable(action):
                should_await = inspect.iscoroutinefunction(action)
                try:
                    sig = inspect.signature(action)
                    param_count = len(sig.parameters)
                except ValueError:
                    param_count = 0
                if self._check_has_value() and param_count > 0:
                    action = functools.partial(action, new_value)
                    param_count -= 1
                if param_count > 0:
                    action = functools.partial(action, event)
                if should_await:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(action())
                else:
                    action()
                dash.flush_side_effects()

    @classmethod
    def get_annotations(cls) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for c in cls.mro():
            try:
                d.update(**c.__annotations__)
            except AttributeError:
                # object, at least, has no __annotations__ attribute.
                pass
        return d


# Ruff doesn't like how we initialize our fields so we hide that we're using a dataclass
FoolRuff = dataclass


@FoolRuff(kw_only=True)
class ColorMixins:
    background_color: Color | None = widget_field(
        "Background Color", category="Rendering", default=None
    )
    text_color: Color | None = widget_field(
        "Text Color", category="Rendering", default=None
    )


def from_mime_type(bundle: dict) -> BaseWidget:
    cls = widget_class_by_name.get(bundle[BUNDLE_TAG].lower())
    if cls is None:
        raise ValueError(f"Unknown widget type {bundle[BUNDLE_TAG]}")
    copied = copy.deepcopy(bundle)
    copied = {
        k: v
        for k, v in copied.items()
        if k in cls.__dataclass_fields__ or k == VALUE_JSON_FIELD
    }
    if VALUE_JSON_FIELD in copied:
        value = copied.pop(VALUE_JSON_FIELD)
    else:
        value = None
    res = cls(**copied)
    if VALUE_JSON_FIELD in bundle:
        try:
            res.set_value(value, do_trigger=False)
        except ValueError:
            # for dropdowns etc, the value might not be in the choices
            pass
    return res
