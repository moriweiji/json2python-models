from typing import Dict, List

import pytest

from rest_client_gen.dynamic_typing import (DList, DOptional, FloatString, ModelMeta, compile_imports)
from rest_client_gen.models import sort_fields
from rest_client_gen.models.attr import AttrsModelCodeGenerator, METADATA_FIELD_NAME
from rest_client_gen.models.base import generate_code
from test.test_code_generation.test_models_code_generator import model_factory, trim


def field_meta(original_name):
    return f"metadata={{'{METADATA_FIELD_NAME}': '{original_name}'}}"


# Data structure:
# pytest.param id -> {
#   "model" -> (model_name, model_metadata),
#   test_name -> expected, ...
# }
test_data = {
    "base": {
        "model": ("Test", {
            "foo": int,
            "bar": int,
            "baz": float
        }),
        "fields_data": {
            "foo": {
                "name": "foo",
                "type": "int",
                "body": f"attr.ib({field_meta('foo')})"
            },
            "bar": {
                "name": "bar",
                "type": "int",
                "body": f"attr.ib({field_meta('bar')})"
            },
            "baz": {
                "name": "baz",
                "type": "float",
                "body": f"attr.ib({field_meta('baz')})"
            }
        },
        "fields": {
            "imports": "",
            "fields": [
                f"foo: int = attr.ib({field_meta('foo')})",
                f"bar: int = attr.ib({field_meta('bar')})",
                f"baz: float = attr.ib({field_meta('baz')})",
            ]
        },
        "generated": trim(f"""
        import attr
        
        
        @attr.s
        class Test:
            foo: int = attr.ib({field_meta('foo')})
            bar: int = attr.ib({field_meta('bar')})
            baz: float = attr.ib({field_meta('baz')})
        """)
    },
    "complex": {
        "model": ("Test", {
            "foo": int,
            "baz": DOptional(DList(DList(str))),
            # "bar": DOptional(IntString),
            "qwerty": FloatString,
            "asdfg": DOptional(int)
        }),
        "fields_data": {
            "foo": {
                "name": "foo",
                "type": "int",
                "body": f"attr.ib({field_meta('foo')})"
            },
            "baz": {
                "name": "baz",
                "type": "Optional[List[List[str]]]",
                "body": f"attr.ib(factory=list, {field_meta('baz')})"
            },
            # "bar": {
            #     "name": "bar",
            #     "type": "Optional[IntString]",
            #     "body": f"attr.ib(converter=IntString, default=None, {field_meta('bar')})"
            # },
            "qwerty": {
                "name": "qwerty",
                "type": "FloatString",
                "body": f"attr.ib(converter=FloatString, {field_meta('qwerty')})"
            },
            "asdfg": {
                "name": "asdfg",
                "type": "Optional[int]",
                "body": f"attr.ib(default=None, {field_meta('asdfg')})"
            }
        },
        "generated": trim(f"""
        import attr
        from rest_client_gen.dynamic_typing.string_serializable import FloatString
        from typing import List, Optional


        @attr.s
        class Test:
            foo: int = attr.ib({field_meta('foo')})
            qwerty: FloatString = attr.ib(converter=FloatString, {field_meta('qwerty')})
            baz: Optional[List[List[str]]] = attr.ib(factory=list, {field_meta('baz')})
            asdfg: Optional[int] = attr.ib(default=None, {field_meta('asdfg')})
        """)
    }
}

test_data_unzip = {
    test: [
        pytest.param(
            model_factory(*data["model"]),
            data[test],
            id=id
        )
        for id, data in test_data.items()
        if test in data
    ]
    for test in ("fields_data", "fields", "generated")
}


@pytest.mark.parametrize("value,expected", test_data_unzip["fields_data"])
def test_fields_data_attr(value: ModelMeta, expected: Dict[str, dict]):
    gen = AttrsModelCodeGenerator(value)
    required, optional = sort_fields(value)
    for is_optional, fields in enumerate((required, optional)):
        for field in fields:
            field_imports, data = gen.field_data(field, value.type[field], bool(is_optional))
            assert data == expected[field]


@pytest.mark.parametrize("value,expected", test_data_unzip["fields"])
def test_fields_attr(value: ModelMeta, expected: dict):
    expected_imports: str = expected["imports"]
    expected_fields: List[str] = expected["fields"]
    gen = AttrsModelCodeGenerator(value)
    imports, fields = gen.fields
    imports = compile_imports(imports)
    assert imports == expected_imports
    assert fields == expected_fields


@pytest.mark.parametrize("value,expected", test_data_unzip["generated"])
def test_generated_attr(value: ModelMeta, expected: str):
    generated = generate_code(([{"model": value, "nested": []}], {}), AttrsModelCodeGenerator)
    assert generated.rstrip() == expected, generated
