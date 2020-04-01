(module
  (import "loader_load_wasm_target" "dependency" (func (result i32)))
  (func (export "call_dependency") (result i32)
    call 0)
)
