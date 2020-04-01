(module
  (import "loader_python_target" "answer" (func $python (result i32)))
  (func (export "call_python") (result i32)
    call $python)
)
