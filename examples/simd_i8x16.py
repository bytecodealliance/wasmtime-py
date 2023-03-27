"""
how to call v128 SMID operations
for more details see https://github.com/WebAssembly/simd/blob/main/proposals/simd/SIMD.md#integer-addition
"""
import ctypes

from functools import partial
from wasmtime import Store, Module, Instance



store = Store()
module = Module(store.engine, """
(module
  (func $add_v128 (param $a v128) (param $b v128) (result v128)
    local.get $a
    local.get $b
    i8x16.add
  )
  (export "add_v128" (func $add_v128))
)
""")

instance = Instance(store, module, [])
vector_type = ctypes.c_uint8*16
add_v128 = partial(instance.exports(store)["add_v128"], store)
a=vector_type(*(i for i in range(16)))
b=vector_type(*(40+i for i in range(16)))
c=add_v128(a, b)
print([v for v in c])
