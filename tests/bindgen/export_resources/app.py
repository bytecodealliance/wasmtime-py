import sys
from types import ModuleType


class MyInterfaceName:
    def interface_func(self, foo: str) -> str:
        return f"hello {foo}"


# componentize-py expects that resources within an interface are defined
# as a class in a separate module that matches the interface name.
#
# Normally, you'd want to go the more typical route of running
#
#   componentize-py -d component.wit -w testworld bindings .
#
# to generate the types and protocols to help you write guest code,
# and then split the code into multiple files, but we're taking a
# shortcut here so we can write all the guest code in a single file.
class DemoResourceClass:
    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self, greeting: str) -> str:
        return f'{greeting}, {self.name}!'


mod = ModuleType("my_interface_name")
mod.DemoResourceClass = DemoResourceClass
sys.modules['my_interface_name'] = mod
