from . import bindgen
from wasmtime import Store

module = """
(component
  (core module $core-mod
    (import "[export]component:basicresource/my-interface-name" "[resource-drop]demo-resource-class" (func $resource-drop (param i32)))
    (import "[export]component:basicresource/my-interface-name" "[resource-new]demo-resource-class" (func $resource-new (param i32) (result i32)))
    (func $core-create-demo-resource (param i32 i32) (result i32)
      unreachable
    )
    (func $core-demo-resource-greet (param i32 i32 i32) (result i32)
      unreachable
    )
    (func $core-cabi-realloc (param i32 i32 i32 i32) (result i32)
      unreachable
    )
    (memory (;0;) 0)
    (export "component:basicresource/my-interface-name#[constructor]demo-resource-class" (func $core-create-demo-resource))
    (export "component:basicresource/my-interface-name#[method]demo-resource-class.greet" (func $core-demo-resource-greet))
    (export "memory" (memory 0))
    (export "cabi_realloc" (func $core-cabi-realloc))
  )
  (type $demo-resource-type (resource (rep i32)))
  (core func $core-resource-drop (canon resource.drop $demo-resource-type))
  (core func $core-resource-rep (canon resource.rep $demo-resource-type))
  (core func $core-resource-new (canon resource.new $demo-resource-type))
  (core instance $canon-instance
    (export "[resource-drop]demo-resource-class" (func $core-resource-drop))
    (export "[resource-new]demo-resource-class" (func $core-resource-new))
  )
  (core instance $core-instance (instantiate $core-mod
      (with "[export]component:basicresource/my-interface-name" (instance $canon-instance))
    )
  )
  (alias core export $core-instance "memory" (core memory (;0;)))
  (alias core export $core-instance "cabi_realloc" (core func $cabi-realloc))
  (type $constructor-type (func (param "name" string) (result (own $demo-resource-type))))
  (alias core export $core-instance "component:basicresource/my-interface-name#[constructor]demo-resource-class" (core func $core-constructor))
  (func $lift-demo-resource-constructor (type $constructor-type) (canon lift (core func $core-constructor) (memory 0) (realloc $cabi-realloc) string-encoding=utf8))
  (type $greet-type (func (param "self" (borrow $demo-resource-type)) (param "greeting" string) (result string)))
  (alias core export $core-instance "component:basicresource/my-interface-name#[method]demo-resource-class.greet" (core func $core-greet))
  (func $lift-demo-resource-greet (type $greet-type) (canon lift (core func $core-greet) (memory 0) (realloc $cabi-realloc) string-encoding=utf8))
  (component $comp-api
    (import "import-type-demo-resource-class" (type $demo-resource (sub resource)))
    (type $constructor-type (func (param "name" string) (result (own $demo-resource))))
    (import "import-constructor-demo-resource-class" (func $constructor-import (type $constructor-type)))
    (type $greet-type (func (param "self" (borrow $demo-resource)) (param "greeting" string) (result string)))
    (import "import-method-demo-resource-class-greet" (func $greet-import (type $greet-type)))
    (export $demo-resource-export "demo-resource-class" (type $demo-resource))
    (type $constructor-type-export (func (param "name" string) (result (own $demo-resource-export))))
    (export "[constructor]demo-resource-class" (func $constructor-import) (func (type $constructor-type-export)))
    (type $greet-type-export (func (param "self" (borrow $demo-resource-export)) (param "greeting" string) (result string)))
    (export "[method]demo-resource-class.greet" (func $greet-import) (func (type $greet-type-export)))
  )
  (instance $api-instance (instantiate $comp-api
      (with "import-constructor-demo-resource-class" (func $lift-demo-resource-constructor))
      (with "import-method-demo-resource-class-greet" (func $lift-demo-resource-greet))
      (with "import-type-demo-resource-class" (type $demo-resource-type))
    )
  )
  (export "component:basicresource/my-interface-name" (instance $api-instance))
)
"""

bindgen("export_resources", module)

from .generated.export_resources import Root
from .generated.export_resources import my_interface_name


def test_bindings():
    store = Store()
    root = Root(store)
    interface = root.my_interface_name()
    # We can't test round tripping until support for resource imports
    # is added.  For now, we can check that the structure of the
    # generated code looks right.
    assert hasattr(interface, "DemoResourceClass")
    assert hasattr(my_interface_name, "DemoResourceClass")
    resource_cls = my_interface_name.DemoResourceClass
    assert resource_cls.greet.__annotations__ == {
        "caller": Store,
        "greeting": str,
        "return": str,
    }
