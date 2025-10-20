# type: ignore

# This is a small script to parse the header files from wasmtime and generate
# appropriate function definitions in Python for each exported function. This
# also reflects types into Python with `ctypes`. While there's at least one
# other generate that does this already it seemed to not quite fit our purposes
# with lots of extra an unnecessary boilerplate.

from pycparser import c_ast, parse_file
import sys

class Visitor(c_ast.NodeVisitor):
    def __init__(self):
        self.ret = ''
        self.ret += '# flake8: noqa\n'
        self.ret += '#\n'
        self.ret += '# This is a procedurally generated file, DO NOT EDIT\n'
        self.ret += '# instead edit `./ci/cbindgen.py` at the root of the repo\n'
        self.ret += '\n'
        self.ret += 'from ctypes import *\n'
        self.ret += 'import ctypes\n'
        self.ret += 'from typing import Any\n'
        self.ret += 'from enum import Enum, auto\n'
        self.ret += 'from ._ffi import dll, wasm_val_t, wasm_ref_t\n'
        self.forward_declared = {}

    # Skip all function definitions, we don't bind those
    def visit_FuncDef(self, node):
        pass

    def visit_Struct(self, node):
        if not node.name or not node.name.startswith('was'):
            return

        # This is hand-generated since it has an anonymous union in it
        if node.name == 'wasm_val_t' or node.name == 'wasm_ref_t':
            return

        self.ret += "\n"
        if not node.decls:
            self.forward_declared[node.name] = True
            self.ret += "class {}(Structure):\n".format(node.name)
            self.ret += "    pass\n"
            return

        anon_decl = 0
        for decl in node.decls:
            if not decl.name:
                assert(isinstance(decl.type, c_ast.Struct))
                decl.type.name = node.name + '_anon_' + str(anon_decl)
                self.visit_Struct(decl.type)
                anon_decl += 1
                decl.name = '_anon_' + str(anon_decl)

        if node.name in self.forward_declared:
            self.ret += "{}._fields = [ # type: ignore\n".format(node.name)
        else:
            self.ret += "class {}(Structure):\n".format(node.name)
            self.ret += "    _fields_ = [\n"

        for decl in node.decls:
            self.ret += "        (\"{}\", {}),\n".format(decl.name, type_name(decl.type))
        self.ret += "    ]\n"

        if not node.name in self.forward_declared:
            for decl in node.decls:
                self.ret += "    {}: {}\n".format(decl.name, type_name(decl.type, typing=True))

    def visit_Union(self, node):
        if not node.name or not node.name.startswith('was'):
            return
        assert(node.decls)

        self.ret += "\n"
        self.ret += "class {}(Union):\n".format(node.name)
        self.ret += "    _fields_ = [\n"
        for decl in node.decls:
            self.ret += "        (\"{}\", {}),\n".format(name(decl.name), type_name(decl.type))
        self.ret += "    ]\n"
        for decl in node.decls:
            self.ret += "    {}: {}".format(name(decl.name), type_name(decl.type, typing=True))
            if decl.name == 'v128':
                self.ret += '  # type: ignore'
            self.ret += "\n"

    def visit_Enum(self, node):
        if not node.name or not node.name.startswith('was'):
            return

        self.ret += "\n"
        self.ret += "class {}(Enum):\n".format(node.name)
        for enumerator in node.values.enumerators:
            if enumerator.value:
                self.ret += "    {} = {}\n".format(enumerator.name, enumerator.value.value)
            else:
                self.ret += "    {} = auto()\n".format(enumerator.name)


    def visit_Typedef(self, node):
        if not node.name or not node.name.startswith('was'):
            return

        # Given anonymous structs in typedefs names by default.
        if isinstance(node.type, c_ast.TypeDecl):
            if isinstance(node.type.type, c_ast.Struct) or \
                isinstance(node.type.type, c_ast.Union):
                if node.type.type.name is None:
                    if node.name.endswith('_t'):
                        node.type.type.name = node.name[:-2]

        self.visit(node.type)
        tyname = type_name(node.type)
        if tyname != node.name:
            self.ret += "\n"
            if isinstance(node.type, c_ast.ArrayDecl):
                self.ret += "{} = {} * {}\n".format(node.name, type_name(node.type.type), node.type.dim.value)
            else:
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

        # This function forward-declares `wasm_instance_t` which doesn't work
        # with this binding generator, but for now this isn't used anyway so
        # just skip it.
        if name == 'wasm_frame_instance':
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
                tyname = type_name(param.type)
                if i == 0 and tyname == "None":
                    continue
                argpairs.append("{}: Any".format(argname))
                argnames.append(argname)
                argtypes.append(tyname)

        # It seems like this is the actual return value of the function, not a
        # pointer. Special-case this so the type-checking agrees with runtime.
        if type_name(ret, ptr) == 'c_void_p':
            retty = 'int'
        else:
            retty = type_name(node.type, ptr, typing=True)

        self.ret += "\n"
        self.ret += "_{0} = dll.{0}\n".format(name)
        self.ret += "_{}.restype = {}\n".format(name, type_name(ret, ptr))
        self.ret += "_{}.argtypes = [{}]\n".format(name, ', '.join(argtypes))
        self.ret += "def {}({}) -> {}:\n".format(name, ', '.join(argpairs), retty)
        self.ret += "    return _{}({})  # type: ignore\n".format(name, ', '.join(argnames))


def name(name):
    if name == 'global':
        return 'global_'
    return name


def type_name(ty, ptr=False, typing=False):
    while isinstance(ty, c_ast.TypeDecl):
        ty = ty.type

    if ptr:
        if typing:
            return "ctypes._Pointer"
        if isinstance(ty, c_ast.IdentifierType) and ty.names[0] == "void":
            return "c_void_p"
        elif not isinstance(ty, c_ast.FuncDecl):
            return "POINTER({})".format(type_name(ty, False, typing))

    if isinstance(ty, c_ast.IdentifierType):
        assert(len(ty.names) == 1)
        if ty.names[0] == "void":
            return "None"
        elif ty.names[0] == "_Bool":
            return "bool" if typing else "c_bool"
        elif ty.names[0] == "byte_t":
            return "c_ubyte"
        elif ty.names[0] == "int8_t":
            return "c_int8"
        elif ty.names[0] == "uint8_t":
            return "c_uint8"
        elif ty.names[0] == "int16_t":
            return "c_int16"
        elif ty.names[0] == "uint16_t":
            return "c_uint16"
        elif ty.names[0] == "int32_t":
            return "int" if typing else "c_int32"
        elif ty.names[0] == "uint32_t":
            return "int" if typing else "c_uint32"
        elif ty.names[0] == "uint64_t":
            return "int" if typing else "c_uint64"
        elif ty.names[0] == "int64_t":
            return "int" if typing else "c_int64"
        elif ty.names[0] == "float32_t":
            return "float" if typing else "c_float"
        elif ty.names[0] == "float64_t":
            return "float" if typing else "c_double"
        elif ty.names[0] == "size_t":
            return "int" if typing else "c_size_t"
        elif ty.names[0] == "char":
            return "c_char"
        elif ty.names[0] == "int":
            return "int" if typing else "c_int"
        # ctypes values can't stand as typedefs, so just use the pointer type here
        elif typing and 'callback_t' in ty.names[0]:
            return "ctypes._Pointer"
        elif typing and ('size' in ty.names[0] or 'pages' in ty.names[0]):
            return "int"
        return ty.names[0]
    elif isinstance(ty, c_ast.Struct):
        return ty.name
    elif isinstance(ty, c_ast.Union):
        return ty.name
    elif isinstance(ty, c_ast.Enum):
        return ty.name
    elif isinstance(ty, c_ast.FuncDecl):
        tys = []
        # TODO: apparently errors are thrown if we faithfully represent the
        # pointer type here, seems odd?
        if isinstance(ty.type, c_ast.PtrDecl):
            tys.append("c_size_t")
        else:
            tys.append(type_name(ty.type))
        if ty.args and ty.args.params:
            for param in ty.args.params:
                tys.append(type_name(param.type))
        return "CFUNCTYPE({})".format(', '.join(tys))
    elif isinstance(ty, c_ast.PtrDecl) or isinstance(ty, c_ast.ArrayDecl):
        return type_name(ty.type, True, typing)
    else:
        raise RuntimeError("unknown {}".format(ty))


def run():
    ast = parse_file(
        './wasmtime/include/wasmtime.h',
        use_cpp=True,
        cpp_path='gcc',
        cpp_args=[
            '-E',
            '-I./wasmtime/include',
            '-D__attribute__(x)=',
            '-D__asm__(x)=',
            '-D__asm(x)=',
            '-D__volatile__(x)=',
            '-D_Static_assert(x, y)=',
            '-Dstatic_assert(x, y)=',
            '-D__restrict=',
            '-D__restrict__=',
            '-D__extension__=',
            '-D__inline__=',
            '-D__signed=',
            '-D__builtin_va_list=int',
        ]
    )

    v = Visitor()
    v.visit(ast)
    return v.ret

if __name__ == "__main__":
    with open("wasmtime/_bindings.py", "w") as f:
        f.write(run())
elif sys.platform == 'linux':
    with open("wasmtime/_bindings.py", "r") as f:
        contents = f.read()
        if contents != run():
            raise RuntimeError("bindings need an update, run this script")
