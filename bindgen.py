# type: ignore

# This is a small script to parse the header files from wasmtime and generate
# appropriate function definitions in Python for each exported function. This
# also reflects types into Python with `ctypes`. While there's at least one
# other generate that does this already it seemed to not quite fit our purposes
# with lots of extra an unnecessary boilerplate.

from pycparser import c_ast, parse_file


class Visitor(c_ast.NodeVisitor):
    def __init__(self):
        self.ret = ''
        self.ret += '# flake8: noqa\n'
        self.ret += '#\n'
        self.ret += '# This is a procedurally generated file, DO NOT EDIT\n'
        self.ret += '# instead edit `./bindgen.py` at the root of the repo\n'
        self.ret += '\n'
        self.ret += 'from ctypes import *\n'
        self.ret += 'from typing import Any\n'
        self.ret += 'from ._ffi import dll, wasm_val_t\n'
        self.generated_wasm_ref_t = False

    # Skip all function definitions, we don't bind those
    def visit_FuncDef(self, node):
        pass

    def visit_Struct(self, node):
        if not node.name or not node.name.startswith('was'):
            return

        # This is hand-generated since it has an anonymous union in it
        if node.name == 'wasm_val_t':
            return

        # This is defined twice in the header file, but we only want to insert
        # one definition.
        if node.name == 'wasm_ref_t':
            if self.generated_wasm_ref_t:
                return
            self.generated_wasm_ref_t = True

        self.ret += "\n"
        self.ret += "class {}(Structure):\n".format(node.name)
        if node.decls:
            self.ret += "    _fields_ = [\n"
            for decl in node.decls:
                self.ret += "        (\"{}\", {}),\n".format(decl.name, type_name(decl.type))
            self.ret += "    ]\n"
        else:
            self.ret += "    pass\n"

    def visit_Typedef(self, node):
        if not node.name or not node.name.startswith('was'):
            return
        self.visit(node.type)
        tyname = type_name(node.type)
        if tyname != node.name:
            self.ret += "\n"
            self.ret += "{} = {}\n".format(node.name, type_name(node.type))

    def visit_FuncDecl(self, node):
        if isinstance(node.type, c_ast.TypeDecl):
            ptr = False
            ty = node.type
        elif isinstance(node.type, c_ast.PtrDecl):
            ptr = True
            ty = node.type.type
        name = ty.declname
        # This is probably a type, skip it
        if name.endswith('_t'):
            return
        # Skip anything not related to wasi or wasm
        if not name.startswith('was'):
            return

        # TODO: these are bugs with upstream wasmtime
        if name == 'wasm_frame_copy':
            return
        if name == 'wasm_frame_instance':
            return
        if name == 'wasm_module_serialize':
            return
        if name == 'wasm_module_deserialize':
            return
        if 'ref_as_' in name:
            return
        if 'extern_const' in name:
            return
        if 'foreign' in name:
            return

        ret = ty.type

        argpairs = []
        argtypes = []
        argnames = []
        if node.args:
            for i, param in enumerate(node.args.params):
                argname = param.name
                if not argname or argname == "import" or argname == "global":
                    argname = "arg{}".format(i)
                argpairs.append("{}: Any".format(argname))
                argnames.append(argname)
                argtypes.append(type_name(param.type))
        retty = type_name(node.type, ptr, typing=True)

        self.ret += "\n"
        self.ret += "_{0} = dll.{0}\n".format(name)
        self.ret += "_{}.restype = {}\n".format(name, type_name(ret, ptr))
        self.ret += "_{}.argtypes = [{}]\n".format(name, ', '.join(argtypes))
        self.ret += "def {}({}) -> {}:\n".format(name, ', '.join(argpairs), retty)
        self.ret += "    return _{}({})  # type: ignore\n".format(name, ', '.join(argnames))


def type_name(ty, ptr=False, typing=False):
    while isinstance(ty, c_ast.TypeDecl):
        ty = ty.type

    if ptr:
        if typing:
            return "pointer"
        if isinstance(ty, c_ast.IdentifierType) and ty.names[0] == "void":
            return "c_void_p"
        elif not isinstance(ty, c_ast.FuncDecl):
            return "POINTER({})".format(type_name(ty, False, typing))

    if isinstance(ty, c_ast.IdentifierType):
        assert(len(ty.names) == 1)
        if ty.names[0] == "void":
            return "None"
        elif ty.names[0] == "_Bool":
            return "c_bool"
        elif ty.names[0] == "byte_t":
            return "c_ubyte"
        elif ty.names[0] == "uint8_t":
            return "c_uint8"
        elif ty.names[0] == "uint32_t":
            return "int" if typing else "c_uint32"
        elif ty.names[0] == "uint64_t":
            return "c_uint64"
        elif ty.names[0] == "size_t":
            return "int" if typing else "c_size_t"
        elif ty.names[0] == "char":
            return "c_char"
        elif ty.names[0] == "int":
            return "int" if typing else "c_int"
        # ctypes values can't stand as typedefs, so just use the pointer type here
        elif typing and 'func_callback' in ty.names[0]:
            return "pointer"
        elif typing and ('size' in ty.names[0] or 'pages' in ty.names[0]):
            return "int"
        return ty.names[0]
    elif isinstance(ty, c_ast.Struct):
        return ty.name
    elif isinstance(ty, c_ast.FuncDecl):
        tys = []
        # TODO: apparently errors are thrown if we faithfully represent the
        # pointer type here, seems odd?
        if isinstance(ty.type, c_ast.PtrDecl):
            tys.append("c_size_t")
        else:
            tys.append(type_name(ty.type))
        if ty.args.params:
            for param in ty.args.params:
                tys.append(type_name(param.type))
        return "CFUNCTYPE({})".format(', '.join(tys))
    elif isinstance(ty, c_ast.PtrDecl) or isinstance(ty, c_ast.ArrayDecl):
        return type_name(ty.type, True, typing)
    else:
        raise RuntimeError("unknown {}".format(ty))


ast = parse_file(
    './wasmtime/include/wasmtime.h',
    use_cpp=True,
    cpp_args=[
        '-I./wasmtime/include',
        '-D__attribute__(x)=',
        '-D__asm__(x)=',
        '-D_Static_assert(x, y)=',
        '-Dstatic_assert(x, y)=',
        '-D__restrict=',
        '-D__extension__=',
    ]
)

v = Visitor()
v.visit(ast)

if __name__ == "__main__":
    with open("wasmtime/_bindings.py", "w") as f:
        f.write(v.ret)
else:
    with open("wasmtime/_bindings.py", "r") as f:
        contents = f.read()
        if contents != v.ret:
            raise RuntimeError("bindings need an update, run this script")
