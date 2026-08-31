"""Tests the blueprint's HTTP endpoint."""

from repo_dashboard.my_cool_object import MyCoolObject


def test_my_cool_object() -> None:
    my_obj = MyCoolObject("Hello, World!")
    assert my_obj.get_message() == "Hello, World!"


def test_my_cool_object_fixture(my_cool_object: MyCoolObject) -> None:
    assert my_cool_object.get_message() == "Hello, World!"
