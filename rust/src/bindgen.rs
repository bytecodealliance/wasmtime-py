//! Code generator for the `wasmtime` PyPI package.
//!
//! This crate will generate bindings for a single component, like JS, for
//! Python source code. Component-model types are translated to Python and the
//! component is executed using the `wasmtime` PyPI package which is bindings to
//! the `wasmtime` C API which is built on the `wasmtime` Rust API.
//!
//! The generated structure of the bindings looks like follows:
//!
//! ```ignore
//! out_dir/
//!     __init__.py
//!     types.py                # types shared by all imports/exports
//!     imports/                # only present if interfaces are imported
//!         __init__.py         # reexports `Foo` protocols for each interface
//!         foo.py              # types and definitions specific to interface `foo`
//!         ..
//!     exports/                # only present with exported interfaces
//!         __init__.py         # empty file
//!         bar.py              # contains `Bar` as the exported interface
//!         ..
//! ```
//!
//! The top-level `__init__.py` contains a `class Foo` where `Foo` is the name
//! of the component. It contains top-level functions for all top-level exports
//! and exported instances are modeled as a method which returns a struct from
//! `exports/*.py`.

use crate::files::Files;
use crate::ns::Ns;
use crate::source::{self, Source};
use anyhow::{bail, Context, Result};
use heck::*;
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::fmt::Write;
use std::mem;
use wasmtime_environ::component::{
    CanonicalOptions, Component, ComponentTypes, ComponentTypesBuilder, CoreDef, CoreExport,
    Export, ExportItem, GlobalInitializer, InstantiateModule, InterfaceType, LoweredIndex,
    RuntimeImportIndex, RuntimeInstanceIndex, StaticModuleIndex, StringEncoding, Trampoline,
    TrampolineIndex, Translator, TypeFuncIndex, TypeResourceTableIndex,
};
use wasmtime_environ::prelude::*;
use wasmtime_environ::{EntityIndex, ModuleTranslation, PrimaryMap, ScopeVec, Tunables};
use wit_bindgen_core::abi::{self, AbiVariant, Bindgen, Bitcast, Instruction, LiftLower, WasmType};
use wit_component::DecodedWasm;
use wit_parser::*;

/// The name under which to group "bare" host functions (i.e. those imported
/// directly by the world rather than via an interface).
const BARE_FUNCTION_NAMESPACE: &str = "host";

#[derive(Default)]
pub struct WasmtimePy {
    // `$out_dir/__init__.py`
    init: Source,
    // `$out_dir/types.py`
    types: Source,
    // `$out_dir/intrinsics.py`
    intrinsics: Source,
    // `$out_dir/imports/__init__.py`
    imports_init: Source,
    // `$out_dir/exports/$name.py`
    exports: BTreeMap<String, Source>,

    /// Known imported interfaces to have as an argument to construction of the
    /// main component.
    imports: Vec<String>,

    /// All intrinsics emitted to `self.intrinsics` so far.
    all_intrinsics: BTreeSet<&'static str>,

    sizes: SizeAlign,

    imported_interfaces: HashMap<InterfaceId, String>,
    exported_interfaces: HashMap<InterfaceId, String>,

    lowerings: PrimaryMap<LoweredIndex, (TrampolineIndex, TypeFuncIndex, CanonicalOptions)>,
    resource_trampolines: Vec<(TrampolineIndex, Trampoline)>,
}

pub type ResourceMap = BTreeMap<TypeId, ResourceTable>;

pub struct ResourceTable {
    pub data: ResourceData,
}

pub enum ResourceData {
    Host { tid: TypeResourceTableIndex },
}

pub fn dealias(resolve: &Resolve, mut id: TypeId) -> TypeId {
    loop {
        match &resolve.types[id].kind {
            TypeDefKind::Type(Type::Id(that_id)) => id = *that_id,
            _ => break id,
        }
    }
}

impl WasmtimePy {
    /// Generate bindings to load and instantiate the specific binary component
    /// provided.
    pub fn generate(&mut self, _name: &str, binary: &[u8], files: &mut Files) -> Result<()> {
        // Use the `wit-component` crate here to parse `binary` and discover
        // the type-level descriptions and `Interface`s corresponding to the
        // component binary. This is effectively a step that infers a "world" of
        // a component. Right now `interfaces` is a world-like thing and this
        // will likely change as worlds are iterated on in the component model
        // standard. Regardless though this is the step where types are learned
        // and `Interface`s are constructed for further code generation below.
        let (resolve, id) = match wit_component::decode(binary)
            .context("failed to extract interface information from component")?
        {
            DecodedWasm::Component(resolve, world) => (resolve, world),
            DecodedWasm::WitPackage(..) => bail!("expected a component"),
        };
        self.sizes.fill(&resolve);

        // Components are complicated, there's no real way around that. To
        // handle all the work of parsing a component and figuring out how to
        // instantiate core wasm modules and such all the work is offloaded to
        // Wasmtime itself. This crate generator is based on Wasmtime's
        // low-level `wasmtime-environ` crate which is technically not a public
        // dependency but the same author who worked on that in Wasmtime wrote
        // this as well so... "seems fine".
        //
        // Note that we're not pulling in the entire Wasmtime engine here,
        // moreso just the "spine" of validating a component. This enables using
        // Wasmtime's internal `Component` representation as a much easier to
        // process version of a component that has decompiled everything
        // internal to a component to a straight linear list of initializers
        // that need to be executed to instantiate a component.
        let scope = ScopeVec::new();
        let tunables = Tunables::default_u64();
        let mut validator = wasmtime_environ::wasmparser::Validator::new();
        let mut types = ComponentTypesBuilder::new(&validator);
        let (component, modules) = Translator::new(&tunables, &mut validator, &mut types, &scope)
            .translate(binary)
            .context("failed to parse the input component")?;
        let world = &resolve.worlds[id];

        // Insert all core wasm modules into the generated `Files` which will
        // end up getting used in the `generate_instantiate` method.
        for (i, module) in modules.iter() {
            files.push(&self.core_file_name(&world.name, i.as_u32()), module.wasm);
        }

        // With all that prep work delegate to `generate` here
        // to generate all the type-level descriptions for this component now
        // that the interfaces in/out are understood.
        let mut root_functions = Vec::new();
        for (world_key, world_item) in world.imports.clone().into_iter() {
            match world_item {
                WorldItem::Function(function) => root_functions.push(function),
                WorldItem::Interface { id, .. } => {
                    let interface = &resolve.interfaces[id];
                    let iface_name = match world_key {
                        WorldKey::Name(name) => name,
                        WorldKey::Interface(_) => interface.name.as_ref().unwrap().to_string(),
                    };
                    self.import_interface(&resolve, &iface_name, id, files)
                }
                WorldItem::Type(_) => unimplemented!(),
            }
        }
        if !root_functions.is_empty() {
            self.import_functions(&resolve, &root_functions);
        }

        for (world_key, export) in world.exports.clone().into_iter() {
            match export {
                WorldItem::Function(_) => {}
                WorldItem::Interface { id, .. } => {
                    let interface = &resolve.interfaces[id];
                    let iface_name = match world_key {
                        WorldKey::Name(name) => name,
                        WorldKey::Interface(_) => interface.name.as_ref().unwrap().to_string(),
                    };
                    self.export_interface(&resolve, &iface_name, id, files)
                }
                WorldItem::Type(_) => unreachable!(),
            }
        }
        self.finish_interfaces(&world, !root_functions.is_empty(), files);

        for (trampoline_index, trampoline) in component.trampolines.iter() {
            match trampoline {
                Trampoline::LowerImport {
                    index,
                    lower_ty,
                    options,
                } => {
                    let i = self
                        .lowerings
                        .push((trampoline_index, *lower_ty, options.clone()));
                    assert_eq!(i, *index);
                }
                Trampoline::Transcoder { .. } => unimplemented!(),
                Trampoline::AlwaysTrap => unimplemented!(),
                Trampoline::ResourceNew(idx) => {
                    self.resource_trampolines
                        .push((trampoline_index, Trampoline::ResourceNew(*idx)));
                }
                Trampoline::ResourceRep(idx) => {
                    self.resource_trampolines
                        .push((trampoline_index, Trampoline::ResourceRep(*idx)));
                }
                Trampoline::ResourceDrop(idx) => {
                    self.resource_trampolines
                        .push((trampoline_index, Trampoline::ResourceDrop(*idx)));
                }
                Trampoline::ResourceEnterCall => unimplemented!(),
                Trampoline::ResourceExitCall => unimplemented!(),
                Trampoline::ResourceTransferOwn => unimplemented!(),
                Trampoline::ResourceTransferBorrow => unimplemented!(),
                Trampoline::TaskBackpressure { .. } => unimplemented!(),
                Trampoline::TaskReturn => unimplemented!(),
                Trampoline::TaskWait { .. } => unimplemented!(),
                Trampoline::TaskPoll { .. } => unimplemented!(),
                Trampoline::TaskYield { .. } => unimplemented!(),
                Trampoline::SubtaskDrop { .. } => unimplemented!(),
                Trampoline::StreamNew { .. } => unimplemented!(),
                Trampoline::StreamRead { .. } => unimplemented!(),
                Trampoline::StreamWrite { .. } => unimplemented!(),
                Trampoline::StreamCancelRead { .. } => unimplemented!(),
                Trampoline::StreamCancelWrite { .. } => unimplemented!(),
                Trampoline::StreamCloseReadable { .. } => unimplemented!(),
                Trampoline::StreamCloseWritable { .. } => unimplemented!(),
                Trampoline::FutureNew { .. } => unimplemented!(),
                Trampoline::FutureRead { .. } => unimplemented!(),
                Trampoline::FutureWrite { .. } => unimplemented!(),
                Trampoline::FutureCancelRead { .. } => unimplemented!(),
                Trampoline::FutureCancelWrite { .. } => unimplemented!(),
                Trampoline::FutureCloseReadable { .. } => unimplemented!(),
                Trampoline::FutureCloseWritable { .. } => unimplemented!(),
                Trampoline::ErrorContextNew { .. } => unimplemented!(),
                Trampoline::ErrorContextDebugMessage { .. } => unimplemented!(),
                Trampoline::ErrorContextDrop { .. } => unimplemented!(),
                Trampoline::AsyncEnterCall => unimplemented!(),
                Trampoline::AsyncExitCall { .. } => unimplemented!(),
                Trampoline::FutureTransfer => unimplemented!(),
                Trampoline::StreamTransfer => unimplemented!(),
                Trampoline::ErrorContextTransfer => unimplemented!(),
            }
        }

        let comp_types = types.finish(&Component::default()).0;
        // And finally generate the code necessary to instantiate the given
        // component to this method using the `Component` that
        // `wasmtime-environ` parsed.
        self.instantiate(&resolve, id, &component.component, &modules, &comp_types);

        self.finish_component(&world.name, files);

        Ok(())
    }

    fn interface<'a>(&'a mut self, resolve: &'a Resolve) -> InterfaceGenerator<'a> {
        InterfaceGenerator {
            gen: self,
            resolve,
            src: Source::default(),
            interface: None,
            at_root: false,
        }
    }

    fn print_some(&mut self) {
        if !self.all_intrinsics.insert("some_type") {
            return;
        }

        self.types.pyimport("dataclasses", "dataclass");
        self.types.pyimport("typing", "TypeVar");
        self.types.pyimport("typing", "Generic");
        self.types.push_str(
            "
                S = TypeVar('S')
                @dataclass
                class Some(Generic[S]):
                    value: S
            ",
        );
    }

    fn print_result(&mut self) {
        if !self.all_intrinsics.insert("result_type") {
            return;
        }

        self.types.pyimport("dataclasses", "dataclass");
        self.types.pyimport("typing", "TypeVar");
        self.types.pyimport("typing", "Generic");
        self.types.pyimport("typing", "Union");
        self.types.push_str(
            "
                T = TypeVar('T')
                @dataclass
                class Ok(Generic[T]):
                    value: T
                E = TypeVar('E')
                @dataclass
                class Err(Generic[E]):
                    value: E

                Result = Union[Ok[T], Err[E]]
            ",
        );
    }

    fn instantiate(
        &mut self,
        resolve: &Resolve,
        id: WorldId,
        component: &Component,
        modules: &PrimaryMap<StaticModuleIndex, ModuleTranslation<'_>>,
        types: &ComponentTypes,
    ) {
        self.init.pyimport("wasmtime", None);

        let world = &resolve.worlds[id];
        let camel = world.name.to_upper_camel_case().escape();
        let imports = if !component.import_types.is_empty() {
            self.init
                .pyimport(".imports", format!("{camel}Imports").as_str());
            format!(", import_object: {camel}Imports")
        } else {
            String::new()
        };

        uwriteln!(self.init, "class {camel}:");
        self.init.indent();

        self.init.push_str("\n");

        uwriteln!(
            self.init,
            "def __init__(self, store: wasmtime.Store{imports}) -> None:"
        );
        self.init.indent();
        let mut i = Instantiator {
            name: &world.name,
            gen: self,
            resolve: &resolve,
            modules,
            component,
            world: id,
            instances: PrimaryMap::default(),
            lifts: 0,
            resource_tables_initialized: vec![false; component.num_resource_tables],
            types,
        };
        i.gen_canon_resources();
        for init in component.initializers.iter() {
            i.global_initializer(init);
        }
        if component.initializers.len() == 0 {
            i.gen.init.push_str("pass\n");
        }
        let (lifts, nested, resource_map) = i.exports(&component);
        i.gen.init.dedent();

        i.generate_lifts(&camel, None, &lifts, &resource_map);
        for (package_name, lifts) in nested {
            let name = match package_name.find("/") {
                Some(pos) => package_name.split_at(pos + 1).1,
                None => &package_name,
            };
            i.generate_lifts(&camel, Some(name), &lifts, &resource_map);
        }
        i.gen.init.dedent();
    }

    fn core_file_name(&mut self, name: &str, idx: u32) -> String {
        format!("{name}.core{idx}.wasm")
    }

    fn finish_component(&mut self, _name: &str, files: &mut Files) {
        if !self.imports_init.is_empty() {
            files.push("imports/__init__.py", self.imports_init.finish().as_bytes());
        }
        if !self.types.is_empty() {
            files.push("types.py", self.types.finish().as_bytes());
        }
        if !self.intrinsics.is_empty() {
            files.push("intrinsics.py", self.intrinsics.finish().as_bytes());
        }

        for (name, src) in self.exports.iter() {
            let snake = name.to_snake_case().escape();
            files.push(&format!("exports/{snake}.py"), src.finish().as_bytes());
        }
        if !self.exports.is_empty() {
            files.push("exports/__init__.py", b"");
        }

        files.push("__init__.py", self.init.finish().as_bytes());
    }

    fn import_interface(
        &mut self,
        resolve: &Resolve,
        name: &str,
        iface: InterfaceId,
        files: &mut Files,
    ) {
        self.imported_interfaces.insert(iface, name.to_string());
        let mut gen = self.interface(resolve);
        gen.interface = Some(iface);
        gen.types(iface);

        // Generate a "protocol" class which I'm led to believe is the rough
        // equivalent of a Rust trait in Python for this imported interface.
        // This will be referenced in the constructor for the main component.
        let camel = format!("Host{}", name.to_upper_camel_case()).escape();
        let snake = name.to_snake_case().escape();
        gen.src.pyimport("typing", "Protocol");
        uwriteln!(gen.src, "class {camel}(Protocol):");
        gen.src.indent();
        for (_, func) in resolve.interfaces[iface].functions.iter() {
            gen.src.pyimport("abc", "abstractmethod");
            gen.src.push_str("@abstractmethod\n");
            gen.print_sig(func, true);
            gen.src.push_str(":\n");
            gen.src.indent();
            gen.src.push_str("raise NotImplementedError\n");
            gen.src.dedent();
        }
        if resolve.interfaces[iface].functions.is_empty() {
            gen.src.push_str("pass\n");
        }
        gen.src.dedent();
        gen.src.push_str("\n");

        let src = gen.src.finish();
        files.push(&format!("imports/{snake}.py"), src.as_bytes());
        self.imports.push(name.to_string());
    }

    fn import_functions(&mut self, resolve: &Resolve, functions: &[Function]) {
        let src = mem::take(&mut self.imports_init);
        let mut gen = self.interface(resolve);
        gen.src = src;

        let camel = BARE_FUNCTION_NAMESPACE.to_upper_camel_case();
        gen.src.pyimport("typing", "Protocol");
        gen.src.pyimport("abc", "abstractmethod");
        uwriteln!(gen.src, "class {camel}(Protocol):");
        gen.src.indent();
        for func in functions.iter() {
            gen.src.push_str("@abstractmethod\n");
            gen.print_sig(func, true);
            gen.src.push_str(":\n");
            gen.src.indent();
            gen.src.push_str("raise NotImplementedError\n");
            gen.src.dedent();
        }
        gen.src.dedent();
        gen.src.push_str("\n");

        self.imports_init = gen.src;
    }

    fn export_interface(
        &mut self,
        resolve: &Resolve,
        name: &str,
        iface: InterfaceId,
        _files: &mut Files,
    ) {
        self.exported_interfaces.insert(iface, name.to_string());
        let mut gen = self.interface(resolve);
        gen.interface = Some(iface);
        gen.types(iface);

        // Only generate types for exports and this will get finished later on
        // as lifted functions need to be inserted into these files as they're
        // discovered.
        let src = gen.src;
        self.exports.insert(name.to_string(), src);
    }

    fn finish_interfaces(&mut self, world: &World, has_root_imports: bool, _files: &mut Files) {
        if has_root_imports || !self.imports.is_empty() {
            let camel = world.name.to_upper_camel_case().escape();
            self.imports_init.pyimport("dataclasses", "dataclass");
            uwriteln!(self.imports_init, "@dataclass");
            uwriteln!(self.imports_init, "class {camel}Imports:");
            self.imports_init.indent();
            if has_root_imports {
                let camel = BARE_FUNCTION_NAMESPACE.to_upper_camel_case();
                let snake = BARE_FUNCTION_NAMESPACE.to_snake_case();
                uwriteln!(self.imports_init, "{snake}: {camel}");
            }
            for import in self.imports.iter() {
                let snake = import.to_snake_case().escape();
                let camel = format!("Host{}", import.to_upper_camel_case()).escape();
                self.imports_init
                    .pyimport(&format!(".{snake}"), camel.as_str());
                uwriteln!(self.imports_init, "{snake}: {camel}");
            }
            self.imports_init.dedent();
        }
    }
}

fn array_ty(resolve: &Resolve, ty: &Type) -> Option<&'static str> {
    match ty {
        Type::Bool => None,
        Type::U8 => Some("c_uint8"),
        Type::S8 => Some("c_int8"),
        Type::U16 => Some("c_uint16"),
        Type::S16 => Some("c_int16"),
        Type::U32 => Some("c_uint32"),
        Type::S32 => Some("c_int32"),
        Type::U64 => Some("c_uint64"),
        Type::S64 => Some("c_int64"),
        Type::F32 => Some("c_float"),
        Type::F64 => Some("c_double"),
        Type::Char => None,
        Type::String => None,
        Type::Id(id) => match &resolve.types[*id].kind {
            TypeDefKind::Type(t) => array_ty(resolve, t),
            _ => None,
        },
    }
}

struct Instantiator<'a> {
    name: &'a str,
    gen: &'a mut WasmtimePy,
    modules: &'a PrimaryMap<StaticModuleIndex, ModuleTranslation<'a>>,
    instances: PrimaryMap<RuntimeInstanceIndex, StaticModuleIndex>,
    world: WorldId,
    component: &'a Component,
    lifts: usize,
    resolve: &'a Resolve,
    resource_tables_initialized: Vec<bool>,
    types: &'a ComponentTypes,
}

struct Lift<'a> {
    callee: String,
    opts: &'a CanonicalOptions,
    func: &'a Function,
    interface: Option<InterfaceId>,
}

impl<'a> Instantiator<'a> {
    fn global_initializer(&mut self, init: &GlobalInitializer) {
        match init {
            GlobalInitializer::InstantiateModule(m) => match m {
                InstantiateModule::Static(idx, args) => self.instantiate_static_module(*idx, args),

                // This is only needed when instantiating an imported core wasm
                // module which while easy to implement here is not possible to
                // test at this time so it's left unimplemented.
                InstantiateModule::Import(..) => unimplemented!(),
            },

            GlobalInitializer::ExtractMemory(m) => {
                let def = self.core_export(&m.export);
                let i = m.index.as_u32();
                uwriteln!(self.gen.init, "core_memory{i} = {def}");
                uwriteln!(
                    self.gen.init,
                    "assert(isinstance(core_memory{i}, wasmtime.Memory))"
                );
                uwriteln!(self.gen.init, "self._core_memory{i} = core_memory{i}",);
            }
            GlobalInitializer::ExtractRealloc(r) => {
                let def = self.core_def(&r.def);
                let i = r.index.as_u32();
                uwriteln!(self.gen.init, "realloc{i} = {def}");
                uwriteln!(
                    self.gen.init,
                    "assert(isinstance(realloc{i}, wasmtime.Func))"
                );
                uwriteln!(self.gen.init, "self._realloc{i} = realloc{i}",);
            }
            GlobalInitializer::ExtractPostReturn(p) => {
                let def = self.core_def(&p.def);
                let i = p.index.as_u32();
                uwriteln!(self.gen.init, "post_return{i} = {def}");
                uwriteln!(
                    self.gen.init,
                    "assert(isinstance(post_return{i}, wasmtime.Func))"
                );
                uwriteln!(self.gen.init, "self._post_return{i} = post_return{i}",);
            }

            GlobalInitializer::LowerImport { index, import } => self.lower_import(*index, *import),

            GlobalInitializer::Resource(_) => {}

            GlobalInitializer::ExtractCallback(_) => unimplemented!(),
        }
    }

    fn gen_canon_resources(&mut self) {
        self.gen_resource_handle_tables();
        for (tid, trampoline) in self.gen.resource_trampolines.iter() {
            let tidx = tid.as_u32();
            match trampoline {
                Trampoline::ResourceNew(rid) => {
                    let resource_id = rid.as_u32();
                    let handle_add = &format!("_handle_add_{resource_id}");
                    uwriteln!(self.gen.init, "def _resource_new_{resource_id}(rep):");
                    self.gen.init.indent();
                    uwriteln!(self.gen.init, "return {handle_add}((rep, True))");
                    self.gen.init.dedent();
                    uwriteln!(
                        self.gen.init,
                        "_resource_new_{resource_id}_ty = wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()])"
                    );
                    uwriteln!(
                        self.gen.init,
                        "trampoline{tidx} = wasmtime.Func(store, _resource_new_{resource_id}_ty, _resource_new_{resource_id})"
                    )
                }
                Trampoline::ResourceDrop(rid) => {
                    let resource_id = rid.as_u32();
                    uwriteln!(self.gen.init, "def _resource_drop_{resource_id}(rep):");
                    self.gen.init.indent();
                    uwriteln!(self.gen.init, "_handle_remove_{resource_id}(rep)");
                    self.gen.init.dedent();
                    uwriteln!(
                        self.gen.init,
                        "_resource_drop_{resource_id}_ty = wasmtime.FuncType([wasmtime.ValType.i32()], [])"
                    );
                    uwriteln!(
                        self.gen.init,
                        "trampoline{tidx} = wasmtime.Func(store, _resource_drop_{resource_id}_ty, _resource_drop_{resource_id})"
                    );
                }
                Trampoline::ResourceRep(rid) => {
                    let resource_id = rid.as_u32();
                    uwriteln!(self.gen.init, "def _resource_rep_{resource_id}(handle):");
                    self.gen.init.indent();
                    uwriteln!(self.gen.init, "return _handle_get_{resource_id}(handle)[0]");
                    self.gen.init.dedent();
                    uwriteln!(
                        self.gen.init,
                        "_resource_rep_{resource_id}_ty = wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()])"
                    );
                    uwriteln!(
                        self.gen.init,
                        "trampoline{tidx} = wasmtime.Func(store, _resource_rep_{resource_id}_ty, _resource_rep_{resource_id})"
                    );
                }
                _ => unreachable!(),
            }
        }
    }

    fn gen_resource_handle_tables(&mut self) {
        let table_indices = self
            .gen
            .resource_trampolines
            .iter()
            .map(|(_, trampoline)| match trampoline {
                Trampoline::ResourceNew(idx)
                | Trampoline::ResourceRep(idx)
                | Trampoline::ResourceDrop(idx) => *idx,
                _ => unreachable!(),
            })
            .collect::<Vec<_>>();
        for table_idx in table_indices {
            self.ensure_resource_table(&table_idx);
        }
    }

    fn ensure_resource_table(&mut self, rid: &TypeResourceTableIndex) {
        let resource_id = rid.as_u32();
        if self.resource_tables_initialized[resource_id as usize] {
            return;
        }
        self.resource_tables_initialized[resource_id as usize] = true;
        self.gen.init.pyimport("typing", "Tuple");
        self.gen.init.pyimport("typing", "List");
        self.gen.init.pyimport("typing", "Optional");
        let table_name = &format!("_handle_table_{resource_id}");
        let free_list = &format!("_handle_table_free{resource_id}");
        uwriteln!(
            self.gen.init,
            "{table_name}: List[Optional[Tuple[int, bool]]] = []"
        );
        uwriteln!(self.gen.init, "{free_list}: List[int] = []");
        let add_entry = &format!(
            "
            def _handle_add_{resource_id}(entry):
                if {free_list}:
                    idx = {free_list}.pop()
                    {table_name}[idx] = entry
                    return idx
                else:
                    {table_name}.append(entry)
                    return len({table_name}) - 1
            self._handle_add_{resource_id} = _handle_add_{resource_id}"
        );
        self.gen.init.push_str(add_entry);
        let remove_entry = &format!(
            "
            def _handle_remove_{resource_id}(i):
                entry = {table_name}[i]
                {table_name}[i] = None
                {free_list}.append(i)
                return entry
            self._handle_remove_{resource_id} = _handle_remove_{resource_id}
        "
        );
        self.gen.init.push_str(remove_entry);
        let get_entry = &format!(
            "
            def _handle_get_{resource_id}(i):
                return {table_name}[i]
            self._handle_get_{resource_id} = _handle_get_{resource_id}
        "
        );
        self.gen.init.push_str(get_entry);
    }

    fn instantiate_static_module(&mut self, idx: StaticModuleIndex, args: &[CoreDef]) {
        let i = self.instances.push(idx);
        let core_file_name = self.gen.core_file_name(&self.name, idx.as_u32());
        self.gen.init.pyimport("pathlib", None);
        self.gen.init.pyimport("importlib_resources", None);

        uwriteln!(
            self.gen.init,
            "file = importlib_resources.files() / ('{}')",
            core_file_name,
        );
        uwriteln!(self.gen.init, "if isinstance(file, pathlib.Path):");
        self.gen.init.indent();
        uwriteln!(
            self.gen.init,
            "module = wasmtime.Module.from_file(store.engine, file)"
        );
        self.gen.init.dedent();
        uwriteln!(self.gen.init, "else:");
        self.gen.init.indent();
        uwriteln!(
            self.gen.init,
            "module = wasmtime.Module(store.engine, file.read_bytes())"
        );
        self.gen.init.dedent();
        uwrite!(
            self.gen.init,
            "instance{} = wasmtime.Instance(store, module, [",
            i.as_u32()
        );
        if !args.is_empty() {
            self.gen.init.push_str("\n");
            self.gen.init.indent();
            for arg in args {
                let def = self.core_def(arg);
                uwriteln!(self.gen.init, "{def},");
            }
            self.gen.init.dedent();
        }
        uwriteln!(self.gen.init, "]).exports(store)");
    }

    fn lower_import(
        &mut self,
        index: LoweredIndex,
        import: RuntimeImportIndex,
        // lower_ty: TypeFuncIndex,
        // options: CanonicalOptions,
    ) {
        // Determine the `Interface` that this import corresponds to. At this
        // time `wit-component` only supports root-level imports of instances
        // where instances export functions.
        let (import_index, path) = &self.component.imports[import];
        let item = &self.resolve.worlds[self.world].imports[import_index.as_u32() as usize];
        let (func, interface, import_name) = match item {
            WorldItem::Function(f) => {
                assert_eq!(path.len(), 0);
                (f, None, BARE_FUNCTION_NAMESPACE.to_snake_case())
            }
            WorldItem::Interface { id, .. } => {
                assert_eq!(path.len(), 1);
                let (import_name, _import_ty) = &self.component.import_types[*import_index];
                let import_name = import_name.replace(":", ".");
                let import_name = match import_name.find("/") {
                    Some(pos) => import_name.split_at(pos + 1).1,
                    None => &import_name,
                }
                .to_snake_case()
                .escape();
                (
                    &self.resolve.interfaces[*id].functions[&path[0]],
                    Some(*id),
                    import_name,
                )
            }
            WorldItem::Type(_) => unimplemented!(),
        };

        let (trampoline_index, _ty, options) = self.gen.lowerings[index].clone();
        let trampoline_index = trampoline_index.as_u32();
        let index = index.as_u32();
        let callee = format!(
            "import_object.{import_name}.{}",
            func.name.to_snake_case().escape()
        );

        // Generate an inline function "closure" which will capture the
        // `imports` argument provided to the constructor of this class and have
        // the core wasm signature for this function. Using prior local
        // variables the function here will perform all liftings/lowerings.
        uwrite!(
            self.gen.init,
            "def lowering{index}_callee(caller: wasmtime.Caller"
        );
        let sig = self.resolve.wasm_signature(AbiVariant::GuestImport, func);
        let mut params = Vec::new();
        for (i, param_ty) in sig.params.iter().enumerate() {
            self.gen.init.push_str(", ");
            let param = format!("arg{i}");
            uwrite!(self.gen.init, "{param}: {}", wasm_ty_typing(*param_ty));
            params.push(param);
        }
        self.gen.init.push_str(") -> ");
        match sig.results.len() {
            0 => self.gen.init.push_str("None"),
            1 => self.gen.init.push_str(wasm_ty_typing(sig.results[0])),
            _ => unimplemented!(),
        }
        self.gen.init.push_str(":\n");
        self.gen.init.indent();

        self.bindgen(
            params,
            callee,
            &options,
            func,
            AbiVariant::GuestImport,
            "self",
            interface,
            true,
            // None is being passed for the resource_map because
            // support for importing resources isn't implemented yet.
            None,
        );
        self.gen.init.dedent();

        // Use the `wasmtime` package's embedder methods of creating a wasm
        // function to finish the construction here.
        uwrite!(self.gen.init, "lowering{index}_ty = wasmtime.FuncType([");
        for param in sig.params.iter() {
            self.gen.init.push_str(wasm_ty_ctor(*param));
            self.gen.init.push_str(", ");
        }
        self.gen.init.push_str("], [");
        for param in sig.results.iter() {
            self.gen.init.push_str(wasm_ty_ctor(*param));
            self.gen.init.push_str(", ");
        }
        self.gen.init.push_str("])\n");
        uwriteln!(
            self.gen.init,
            "trampoline{trampoline_index} = wasmtime.Func(store, lowering{index}_ty, lowering{index}_callee, access_caller = True)"
        );
    }

    fn bindgen(
        &mut self,
        params: Vec<String>,
        callee: String,
        opts: &CanonicalOptions,
        func: &Function,
        abi: AbiVariant,
        this: &str,
        interface: Option<InterfaceId>,
        at_root: bool,
        resource_map: Option<&ResourceMap>,
    ) {
        // Technically it wouldn't be the hardest thing in the world to support
        // other string encodings, but for now the code generator was originally
        // written to support utf-8 so let's just leave it at that for now. In
        // the future when it's easier to produce components with non-utf-8 this
        // can be plumbed through to string lifting/lowering below.
        assert_eq!(opts.string_encoding, StringEncoding::Utf8);

        let memory = match opts.memory {
            Some(idx) => Some(format!("{this}._core_memory{}", idx.as_u32())),
            None => None,
        };
        let realloc = match opts.realloc {
            Some(idx) => Some(format!("{this}._realloc{}", idx.as_u32())),
            None => None,
        };
        let post_return = match opts.post_return {
            Some(idx) => Some(format!("{this}._post_return{}", idx.as_u32())),
            None => None,
        };

        let mut locals = Ns::default();
        locals.insert("len").unwrap(); // python built-in
        locals.insert("base").unwrap(); // may be used as loop var
        locals.insert("i").unwrap(); // may be used as loop var
        let mut gen = InterfaceGenerator {
            // Generate source directly onto `init`
            src: mem::take(&mut self.gen.init),
            gen: self.gen,
            resolve: self.resolve,
            interface,
            at_root,
        };
        let mut f = FunctionBindgen {
            locals,
            payloads: Vec::new(),
            block_storage: Vec::new(),
            blocks: Vec::new(),
            gen: &mut gen,
            callee,
            memory,
            realloc,
            params,
            post_return,
            resource_map,
        };
        abi::call(
            self.resolve,
            abi,
            match abi {
                AbiVariant::GuestImport => LiftLower::LiftArgsLowerResults,
                AbiVariant::GuestExport => LiftLower::LowerArgsLiftResults,
                AbiVariant::GuestImportAsync => unimplemented!(),
                AbiVariant::GuestExportAsync => unimplemented!(),
                AbiVariant::GuestExportAsyncStackful => unimplemented!(),
            },
            func,
            &mut f,
            false,
        );

        // Swap the printed source back into the destination of our `init`, and
        // at this time `f.src` should be empty.
        mem::swap(&mut f.gen.src, &mut f.gen.gen.init);
        assert!(f.gen.src.is_empty());
    }

    fn core_def(&self, def: &CoreDef) -> String {
        match def {
            CoreDef::Export(e) => self.core_export(e),
            CoreDef::Trampoline(i) => format!("trampoline{}", i.as_u32()),
            CoreDef::InstanceFlags(_) => unimplemented!(),
        }
    }

    fn core_export<T>(&self, export: &CoreExport<T>) -> String
    where
        T: Into<EntityIndex> + Copy,
    {
        let name = match &export.item {
            ExportItem::Index(idx) => {
                let module = &self.modules[self.instances[export.instance]].module;
                let idx = (*idx).into();
                module
                    .exports
                    .iter()
                    .filter_map(|(name, i)| if *i == idx { Some(name) } else { None })
                    .next()
                    .unwrap()
            }
            ExportItem::Name(s) => s,
        };
        let i = export.instance.as_u32() as usize;
        format!("instance{i}[\"{name}\"]")
    }

    /// Extract the `LiftedFunction` exports to a format that's easier to
    /// process for this generator. For now all lifted functions are either
    /// "root" lifted functions or one-level-nested for an exported interface.
    ///
    /// As worlds shape up and more of a component's structure is expressible in
    /// `*.wit` this method will likely need to change.
    fn exports(
        &mut self,
        component: &'a Component,
    ) -> (Vec<Lift<'a>>, BTreeMap<&'a str, Vec<Lift<'a>>>, ResourceMap) {
        let mut toplevel = Vec::new();
        let mut nested = BTreeMap::new();
        let mut resource_map = ResourceMap::new();
        let world_exports_by_string = self.resolve.worlds[self.world]
            .exports
            .iter()
            .map(|(k, v)| (self.resolve.name_world_key(k), v))
            .collect::<HashMap<_, _>>();
        for (name, export) in component.exports.raw_iter() {
            let name = name.as_str();
            match &component.export_items[*export] {
                Export::LiftedFunction {
                    ty: _,
                    func,
                    options,
                } => {
                    let callee = self.gen_lift_callee(func);
                    let func = match world_exports_by_string[name] {
                        WorldItem::Function(f) => f,
                        WorldItem::Interface { .. } | WorldItem::Type(_) => unreachable!(),
                    };
                    toplevel.push(Lift {
                        callee,
                        opts: options,
                        func,
                        interface: None,
                    });
                }

                Export::Instance { exports, ty: _ } => {
                    let id = match world_exports_by_string[name] {
                        WorldItem::Interface { id, .. } => *id,
                        WorldItem::Function(_) | WorldItem::Type(_) => unreachable!(),
                    };
                    let mut lifts = Vec::new();
                    for (name, export) in exports.raw_iter() {
                        let export = &component.export_items[*export];
                        let (callee, options, func_ty) = match export {
                            Export::LiftedFunction { func, options, ty } => (func, options, ty),
                            Export::Type(_) => continue,
                            Export::ModuleStatic { .. }
                            | Export::ModuleImport { .. }
                            | Export::Instance { .. } => unreachable!(),
                        };
                        let callee = self.gen_lift_callee(callee);
                        let func = &self.resolve.interfaces[id].functions[name];
                        self.create_resource_fn_map(func, func_ty, &mut resource_map);
                        lifts.push(Lift {
                            callee,
                            opts: options,
                            func,
                            interface: Some(id),
                        });
                    }

                    let prev = nested.insert(name, lifts);
                    assert!(prev.is_none());
                }

                // ignore type exports for now
                Export::Type(_) => {}

                // This can't be tested at this time so leave it unimplemented
                Export::ModuleStatic { .. } | Export::ModuleImport { .. } => unimplemented!(),
            }
        }
        (toplevel, nested, resource_map)
    }

    fn create_resource_fn_map(
        &mut self,
        func: &Function,
        ty_func_idx: &TypeFuncIndex,
        resource_map: &mut ResourceMap,
    ) {
        let params_ty = &self.types[self.types[*ty_func_idx].params];
        let modeled_types = func.params.iter().map(|(_, ty)| ty);
        for (modeled_ty, runtime_ty) in modeled_types.zip(params_ty.types.iter()) {
            if let Type::Id(id) = modeled_ty {
                self.connect_resource_types(*id, runtime_ty, resource_map);
            }
        }
    }

    fn connect_resource_types(
        &mut self,
        id: TypeId,
        iface_ty: &InterfaceType,
        resource_map: &mut ResourceMap,
    ) {
        let kind = &self.resolve.types[id].kind;
        match (kind, iface_ty) {
            (TypeDefKind::Flags(_), InterfaceType::Flags(_))
            | (TypeDefKind::Enum(_), InterfaceType::Enum(_)) => {}
            (TypeDefKind::Record(t1), InterfaceType::Record(t2)) => {
                let t2 = &self.types[*t2];
                for (f1, f2) in t1.fields.iter().zip(t2.fields.iter()) {
                    if let Type::Id(id) = f1.ty {
                        self.connect_resource_types(id, &f2.ty, resource_map);
                    }
                }
            }
            (
                TypeDefKind::Handle(Handle::Own(t1) | Handle::Borrow(t1)),
                InterfaceType::Own(t2) | InterfaceType::Borrow(t2),
            ) => {
                self.connect_resources(*t1, *t2, resource_map);
            }
            (TypeDefKind::Tuple(t1), InterfaceType::Tuple(t2)) => {
                let t2 = &self.types[*t2];
                for (f1, f2) in t1.types.iter().zip(t2.types.iter()) {
                    if let Type::Id(id) = f1 {
                        self.connect_resource_types(*id, f2, resource_map);
                    }
                }
            }
            (TypeDefKind::Variant(t1), InterfaceType::Variant(t2)) => {
                let t2 = &self.types[*t2];
                for (f1, f2) in t1.cases.iter().zip(t2.cases.iter()) {
                    if let Some(Type::Id(id)) = &f1.ty {
                        self.connect_resource_types(*id, f2.1.as_ref().unwrap(), resource_map);
                    }
                }
            }
            (TypeDefKind::Option(t1), InterfaceType::Option(t2)) => {
                let t2 = &self.types[*t2];
                if let Type::Id(id) = t1 {
                    self.connect_resource_types(*id, &t2.ty, resource_map);
                }
            }
            (TypeDefKind::Result(t1), InterfaceType::Result(t2)) => {
                let t2 = &self.types[*t2];
                if let Some(Type::Id(id)) = &t1.ok {
                    self.connect_resource_types(*id, &t2.ok.unwrap(), resource_map);
                }
                if let Some(Type::Id(id)) = &t1.err {
                    self.connect_resource_types(*id, &t2.err.unwrap(), resource_map);
                }
            }
            (TypeDefKind::List(t1), InterfaceType::List(t2)) => {
                let t2 = &self.types[*t2];
                if let Type::Id(id) = t1 {
                    self.connect_resource_types(*id, &t2.element, resource_map);
                }
            }
            (TypeDefKind::Type(ty), _) => {
                if let Type::Id(id) = ty {
                    self.connect_resource_types(*id, iface_ty, resource_map);
                }
            }
            (_, _) => unreachable!(),
        }
    }

    fn connect_resources(
        &mut self,
        t: TypeId,
        tid: TypeResourceTableIndex,
        resource_map: &mut ResourceMap,
    ) {
        self.ensure_resource_table(&tid);
        let entry = ResourceTable {
            data: ResourceData::Host { tid },
        };
        resource_map.insert(t, entry);
    }

    fn gen_lift_callee(&mut self, callee: &CoreDef) -> String {
        // For each lifted function the callee `wasmtime.Func` is
        // saved into a per-instance field which is then referenced
        // as the callee when the relevant function is invoked.
        let def = self.core_def(callee);
        let callee = format!("lift_callee{}", self.lifts);
        self.lifts += 1;
        uwriteln!(self.gen.init, "{callee} = {def}");
        uwriteln!(self.gen.init, "assert(isinstance({callee}, wasmtime.Func))");
        uwriteln!(self.gen.init, "self.{callee} = {callee}");
        callee
    }

    fn generate_lifts(
        &mut self,
        camel_component: &str,
        ns: Option<&str>,
        lifts: &[Lift<'_>],
        resource_map: &ResourceMap,
    ) {
        let mut this = "self".to_string();

        // If these exports are going into a non-default interface then a new
        // `class` is generated in the corresponding file which will be
        // constructed with the "root" class. Generate the class here, its one
        // field of the root class, and then an associated constructor for the
        // root class to have. Finally the root class grows a method here as
        // well to return the nested instance.
        // Any resources and corresponding methods will be generated in separate, individual
        // classes from the class associated with the non-default interface.  This provides a more
        // idiomatic mapping to resources in Python.
        let mut resource_lifts: IndexMap<TypeId, Vec<&Lift<'_>>> = IndexMap::default();
        for lift in lifts {
            if let FunctionKind::Constructor(ty)
            | FunctionKind::Method(ty)
            | FunctionKind::Static(ty) = lift.func.kind
            {
                resource_lifts.entry(ty).or_default().push(lift);
            }
        }
        if let Some(ns) = ns {
            let src = self.gen.exports.get_mut(ns).unwrap();
            let camel = ns.to_upper_camel_case().escape();
            let snake = ns.to_snake_case().escape();
            uwriteln!(src, "class {camel}:");
            src.indent();
            src.typing_import("..", camel_component);
            uwriteln!(src, "component: '{camel_component}'\n");
            uwriteln!(
                src,
                "def __init__(self, component: '{camel_component}') -> None:"
            );
            src.indent();
            uwriteln!(src, "self.component = component");
            // Bind any resource types here in the init so they're available
            // via `self.MyResourceName`.
            for (ty, _) in resource_lifts.iter() {
                let resource_name = self.resolve.types[*ty].name.as_ref().unwrap();
                let cls_name = resource_name.to_upper_camel_case().escape();
                let create_closure_name =
                    format!("_create_{}", resource_name.to_snake_case().escape());
                uwriteln!(src, "self.{cls_name} = {create_closure_name}(component)");
            }
            src.dedent();

            this.push_str(".component");

            self.gen.init.pyimport(".exports", snake.as_str());
            uwriteln!(self.gen.init, "def {snake}(self) -> {snake}.{camel}:");
            self.gen.init.indent();
            uwriteln!(self.gen.init, "return {snake}.{camel}(self)");
            self.gen.init.dedent();

            // Swap the two sources so the generation into `init` will go into
            // the right place
            mem::swap(&mut self.gen.init, src);
        }

        for lift in lifts {
            if let FunctionKind::Constructor(_)
            | FunctionKind::Method(_)
            | FunctionKind::Static(_) = lift.func.kind
            {
                // Function kinds on resources get generated in a separate class
                // specific to the corresponding resource type so we skip them
                // in the top level class for the interface.
                continue;
            }
            // Go through some small gymnastics to print the function signature
            // here.
            let mut gen = InterfaceGenerator {
                resolve: self.resolve,
                src: mem::take(&mut self.gen.init),
                gen: self.gen,
                interface: lift.interface,
                at_root: ns.is_none(),
            };
            let params = gen.print_sig(lift.func, false);
            let src = mem::take(&mut gen.src);
            self.gen.init = src;
            self.gen.init.push_str(":\n");

            // Defer to `self.bindgen` for the body of the function.
            self.gen.init.indent();
            self.gen.init.docstring(&lift.func.docs);
            self.bindgen(
                params,
                format!("{this}.{}", lift.callee),
                lift.opts,
                lift.func,
                AbiVariant::GuestExport,
                &this,
                lift.interface,
                ns.is_none(),
                Some(resource_map),
            );
            self.gen.init.dedent();
        }

        for (resource_ty, lifts) in resource_lifts {
            //
            let resource_name = self.resolve.types[resource_ty].name.as_ref().unwrap();
            let cls_name = resource_name.to_upper_camel_case().escape();
            let create_closure_name = format!("_create_{}", resource_name.to_snake_case().escape());
            self.gen.init.dedent();
            self.gen.init.pyimport("typing", "Type");
            self.gen.init.push_str(&format!(
                "\n\ndef {create_closure_name}(component: 'Root') -> Type[{cls_name}]:\n"
            ));
            self.gen.init.indent();
            self.gen.init.push_str(&format!("class _{cls_name}:\n"));
            self.gen.init.indent();
            for lift in lifts {
                let mut gen = InterfaceGenerator {
                    resolve: self.resolve,
                    src: mem::take(&mut self.gen.init),
                    gen: self.gen,
                    interface: lift.interface,
                    at_root: ns.is_none(),
                };
                let params = gen.print_sig(lift.func, false);
                let src = mem::take(&mut gen.src);
                self.gen.init = src;
                self.gen.init.push_str(":\n");

                // Defer to `self.bindgen` for the body of the function.
                self.gen.init.indent();
                self.gen.init.docstring(&lift.func.docs);
                if let FunctionKind::Constructor(_) = lift.func.kind {
                    // Bind the component from the closure so we can reference it other
                    // methods for this resource.
                    self.gen.init.push_str("self.component = component\n");
                }
                self.bindgen(
                    params,
                    format!("self.component.{}", lift.callee),
                    lift.opts,
                    lift.func,
                    AbiVariant::GuestExport,
                    &this,
                    lift.interface,
                    ns.is_none(),
                    Some(resource_map),
                );
                self.gen.init.dedent();
            }
            self.gen.init.dedent();
            self.gen.init.push_str(&format!("return _{cls_name}"));
        }

        // Undo the swap done above.
        if let Some(ns) = ns {
            mem::swap(&mut self.gen.init, self.gen.exports.get_mut(ns).unwrap());
        }
    }
}

struct InterfaceGenerator<'a> {
    src: Source,
    gen: &'a mut WasmtimePy,
    resolve: &'a Resolve,
    interface: Option<InterfaceId>,
    at_root: bool,
}

impl InterfaceGenerator<'_> {
    fn import_result_type(&mut self) {
        self.gen.print_result();
        self.import_shared_type("Result");
    }

    fn import_some_type(&mut self) {
        self.gen.print_some();
        self.import_shared_type("Some");
    }

    fn print_ty(&mut self, ty: &Type, forward_ref: bool) {
        match ty {
            Type::Bool => self.src.push_str("bool"),
            Type::U8
            | Type::S8
            | Type::U16
            | Type::S16
            | Type::U32
            | Type::S32
            | Type::U64
            | Type::S64 => self.src.push_str("int"),
            Type::F32 | Type::F64 => self.src.push_str("float"),
            Type::Char => self.src.push_str("str"),
            Type::String => self.src.push_str("str"),
            Type::Id(id) => {
                let ty = &self.resolve.types[*id];
                if let Some(name) = &ty.name {
                    let owner = match ty.owner {
                        TypeOwner::Interface(id) => id,
                        _ => unreachable!(),
                    };
                    if Some(owner) == self.interface {
                        let name = self.name_of(name);
                        self.src.push_str(&name);
                    } else {
                        let (module, iface) = match self.gen.imported_interfaces.get(&owner) {
                            Some(name) => ("imports", name),
                            None => (
                                "exports",
                                self.gen.exported_interfaces.get(&owner).unwrap_or(name),
                            ),
                        };
                        let module = if self.at_root {
                            format!(".{module}")
                        } else {
                            format!("..{module}")
                        };
                        let iface = iface.to_snake_case().escape();
                        self.src.pyimport(&module, iface.as_str());
                        uwrite!(
                            self.src,
                            "{iface}.{name}",
                            name = name.to_upper_camel_case().escape()
                        )
                    }
                    return;
                }
                match &ty.kind {
                    TypeDefKind::Type(t) => self.print_ty(t, forward_ref),
                    TypeDefKind::Tuple(t) => self.print_tuple(t),
                    TypeDefKind::Record(_)
                    | TypeDefKind::Flags(_)
                    | TypeDefKind::Enum(_)
                    | TypeDefKind::Variant(_) => {
                        unreachable!()
                    }
                    TypeDefKind::Option(t) => {
                        let nesting = is_option(self.resolve, *t);
                        if nesting {
                            self.import_some_type();
                        }

                        self.src.pyimport("typing", "Optional");
                        self.src.push_str("Optional[");
                        if nesting {
                            self.src.push_str("Some[");
                        }
                        self.print_ty(t, true);
                        if nesting {
                            self.src.push_str("]");
                        }
                        self.src.push_str("]");
                    }
                    TypeDefKind::Result(r) => {
                        self.import_result_type();
                        self.src.push_str("Result[");
                        self.print_optional_ty(r.ok.as_ref(), true);
                        self.src.push_str(", ");
                        self.print_optional_ty(r.err.as_ref(), true);
                        self.src.push_str("]");
                    }
                    TypeDefKind::List(t) => self.print_list(t),
                    TypeDefKind::Future(_) => unimplemented!(),
                    TypeDefKind::Stream(_) => unimplemented!(),
                    TypeDefKind::Resource => unimplemented!(),
                    TypeDefKind::Handle(Handle::Own(t) | Handle::Borrow(t)) => {
                        let ty = &self.resolve.types[*t];
                        // Assuming that handles always refer to a resource type.
                        if let Some(name) = &ty.name {
                            self.src.push_str(&name.to_upper_camel_case().escape());
                        }
                    }
                    TypeDefKind::Unknown => unreachable!(),
                    TypeDefKind::ErrorContext => unimplemented!(),
                }
            }
        }
    }

    fn print_optional_ty(&mut self, ty: Option<&Type>, forward_ref: bool) {
        match ty {
            Some(ty) => self.print_ty(ty, forward_ref),
            None => self.src.push_str("None"),
        }
    }

    fn print_tuple(&mut self, tuple: &Tuple) {
        if tuple.types.is_empty() {
            return self.src.push_str("None");
        }
        self.src.pyimport("typing", "Tuple");
        self.src.push_str("Tuple[");
        for (i, t) in tuple.types.iter().enumerate() {
            if i > 0 {
                self.src.push_str(", ");
            }
            self.print_ty(t, true);
        }
        self.src.push_str("]");
    }

    fn print_list(&mut self, element: &Type) {
        match element {
            Type::U8 => self.src.push_str("bytes"),
            t => {
                self.src.pyimport("typing", "List");
                self.src.push_str("List[");
                self.print_ty(t, true);
                self.src.push_str("]");
            }
        }
    }

    fn print_sig(&mut self, func: &Function, in_import: bool) -> Vec<String> {
        self.src.push_str("def ");
        let func_name = func.item_name().to_snake_case().escape();
        let py_name = match func.kind {
            FunctionKind::Constructor(_) => "__init__",
            _ => &func_name,
        };
        self.src.push_str(py_name);
        if in_import {
            self.src.push_str("(self");
        } else {
            self.src.pyimport("wasmtime", None);
            self.src.push_str("(self, caller: wasmtime.Store");
        }
        let mut params = Vec::new();
        let func_params = match func.kind {
            FunctionKind::Method(_) => {
                // Methods are generated as a separate class where the `self` is already bound
                // to the resource type, so we don't want to add in the signature.
                // However, we still want this as part of the params that are used in
                // FunctionBindgen when generating the lowering to core wasm.
                let self_param = &func.params[0].0;
                params.push(self_param.to_snake_case().escape());
                &func.params[1..]
            }
            _ => &func.params,
        };
        for (param, ty) in func_params.iter() {
            self.src.push_str(", ");
            self.src.push_str(&param.to_snake_case().escape());
            params.push(param.to_snake_case().escape());
            self.src.push_str(": ");
            self.print_ty(ty, true);
        }
        self.src.push_str(") -> ");
        match func.results.len() {
            0 => self.src.push_str("None"),
            1 => match func.kind {
                // The return type of `__init__` in Python is always `None`.
                FunctionKind::Constructor(_) => self.src.push_str("None"),
                _ => self.print_ty(func.results.iter_types().next().unwrap(), true),
            },
            _ => {
                self.src.pyimport("typing", "Tuple");
                self.src.push_str("Tuple[");
                for (i, ty) in func.results.iter_types().enumerate() {
                    if i > 0 {
                        self.src.push_str(", ");
                    }
                    self.print_ty(ty, true);
                }
                self.src.push_str("]");
            }
        }
        params
    }

    fn types(&mut self, interface: InterfaceId) {
        for (name, id) in self.resolve.interfaces[interface].types.iter() {
            let id = *id;
            let ty = &self.resolve.types[id];
            match &ty.kind {
                TypeDefKind::Record(record) => self.type_record(id, name, record, &ty.docs),
                TypeDefKind::Flags(flags) => self.type_flags(id, name, flags, &ty.docs),
                TypeDefKind::Tuple(tuple) => self.type_tuple(id, name, tuple, &ty.docs),
                TypeDefKind::Enum(enum_) => self.type_enum(id, name, enum_, &ty.docs),
                TypeDefKind::Variant(variant) => self.type_variant(id, name, variant, &ty.docs),
                TypeDefKind::Option(t) => self.type_option(id, name, t, &ty.docs),
                TypeDefKind::Result(r) => self.type_result(id, name, r, &ty.docs),
                TypeDefKind::List(t) => self.type_list(id, name, t, &ty.docs),
                TypeDefKind::Type(t) => self.type_alias(id, name, t, &ty.docs),
                TypeDefKind::Future(_) => todo!("generate for future"),
                TypeDefKind::Stream(_) => todo!("generate for stream"),
                TypeDefKind::Resource => self.type_resource(ty, id, name, interface),
                TypeDefKind::Handle(_) => unimplemented!(),
                TypeDefKind::Unknown => unreachable!(),
                TypeDefKind::ErrorContext => unreachable!(),
            }
        }
    }

    fn type_record(&mut self, _id: TypeId, name: &str, record: &Record, docs: &Docs) {
        self.src.pyimport("dataclasses", "dataclass");
        self.src.push_str("@dataclass\n");
        self.src
            .push_str(&format!("class {}:\n", name.to_upper_camel_case().escape()));
        self.src.indent();
        self.src.docstring(docs);
        for field in record.fields.iter() {
            self.src.comment(&field.docs);
            let field_name = field.name.to_snake_case().escape();
            self.src.push_str(&format!("{field_name}: "));
            self.print_ty(&field.ty, true);
            self.src.push_str("\n");
        }
        if record.fields.is_empty() {
            self.src.push_str("pass\n");
        }
        self.src.dedent();
        self.src.push_str("\n");
    }

    fn type_tuple(&mut self, _id: TypeId, name: &str, tuple: &Tuple, docs: &Docs) {
        self.src.comment(docs);
        self.src
            .push_str(&format!("{} = ", name.to_upper_camel_case().escape()));
        self.print_tuple(tuple);
        self.src.push_str("\n");
    }

    fn type_flags(&mut self, _id: TypeId, name: &str, flags: &Flags, docs: &Docs) {
        self.src.pyimport("enum", "Flag");
        self.src.pyimport("enum", "auto");
        self.src.push_str(&format!(
            "class {}(Flag):\n",
            name.to_upper_camel_case().escape()
        ));
        self.src.indent();
        self.src.docstring(docs);
        for flag in flags.flags.iter() {
            let flag_name = flag.name.to_shouty_snake_case();
            self.src.comment(&flag.docs);
            self.src.push_str(&format!("{flag_name} = auto()\n"));
        }
        if flags.flags.is_empty() {
            self.src.push_str("pass\n");
        }
        self.src.dedent();
        self.src.push_str("\n");
    }

    fn type_variant(&mut self, _id: TypeId, name: &str, variant: &Variant, docs: &Docs) {
        self.src.pyimport("dataclasses", "dataclass");
        let mut cases = Vec::new();
        for case in variant.cases.iter() {
            self.src.docstring(&case.docs);
            self.src.push_str("@dataclass\n");
            let case_name = format!(
                "{}{}",
                name.to_upper_camel_case().escape(),
                case.name.to_upper_camel_case().escape()
            );
            self.src.push_str(&format!("class {case_name}:\n"));
            self.src.indent();
            match &case.ty {
                Some(ty) => {
                    self.src.push_str("value: ");
                    self.print_ty(ty, true);
                }
                None => self.src.push_str("pass"),
            }
            self.src.push_str("\n");
            self.src.dedent();
            self.src.push_str("\n");
            cases.push(case_name);
        }

        self.src.pyimport("typing", "Union");
        self.src.comment(docs);
        self.src.push_str(&format!(
            "{} = Union[{}]\n",
            name.to_upper_camel_case().escape(),
            cases.join(", "),
        ));
        self.src.push_str("\n");
    }

    fn type_option(&mut self, _id: TypeId, name: &str, payload: &Type, docs: &Docs) {
        let nesting = is_option(self.resolve, *payload);
        if nesting {
            self.import_some_type();
        }

        self.src.pyimport("typing", "Optional");
        self.src.comment(docs);
        self.src.push_str(&name.to_upper_camel_case().escape());
        self.src.push_str(" = Optional[");
        if nesting {
            self.src.push_str("Some[");
        }
        self.print_ty(payload, true);
        if nesting {
            self.src.push_str("]");
        }
        self.src.push_str("]\n\n");
    }

    fn type_result(&mut self, _id: TypeId, name: &str, result: &Result_, docs: &Docs) {
        self.import_result_type();

        self.src.comment(docs);
        self.src.push_str(&format!(
            "{} = Result[",
            name.to_upper_camel_case().escape()
        ));
        self.print_optional_ty(result.ok.as_ref(), true);
        self.src.push_str(", ");
        self.print_optional_ty(result.err.as_ref(), true);
        self.src.push_str("]\n\n");
    }

    fn type_enum(&mut self, _id: TypeId, name: &str, enum_: &Enum, docs: &Docs) {
        self.src.pyimport("enum", "Enum");
        self.src.push_str(&format!(
            "class {}(Enum):\n",
            name.to_upper_camel_case().escape()
        ));
        self.src.indent();
        self.src.docstring(docs);
        for (i, case) in enum_.cases.iter().enumerate() {
            self.src.comment(&case.docs);

            // TODO this handling of digits should be more general and
            // shouldn't be here just to fix the one case in wasi where an
            // enum variant is "2big" and doesn't generate valid Python. We
            // should probably apply this to all generated Python
            // identifiers.
            let mut name = case.name.to_shouty_snake_case();
            if name.chars().next().unwrap().is_digit(10) {
                name = format!("_{}", name);
            }
            self.src.push_str(&format!("{} = {}\n", name, i));
        }
        self.src.dedent();
        self.src.push_str("\n");
    }

    fn type_alias(&mut self, _id: TypeId, name: &str, ty: &Type, docs: &Docs) {
        self.src.comment(docs);
        self.src
            .push_str(&format!("{} = ", name.to_upper_camel_case().escape()));
        self.print_ty(ty, false);
        self.src.push_str("\n");
    }

    fn type_list(&mut self, _id: TypeId, name: &str, ty: &Type, docs: &Docs) {
        self.src.comment(docs);
        self.src
            .push_str(&format!("{} = ", name.to_upper_camel_case().escape()));
        self.print_list(ty);
        self.src.push_str("\n");
    }

    fn type_resource(&mut self, _ty: &TypeDef, id: TypeId, name: &str, interface: InterfaceId) {
        self.src.pyimport("typing", "Protocol");
        let cls_name = name.to_upper_camel_case().escape();
        let methods = self.resolve.interfaces[interface]
            .functions
            .iter()
            .filter_map(|(_, func)| match func.kind {
                FunctionKind::Method(t)
                | FunctionKind::Static(t)
                | FunctionKind::Constructor(t) => {
                    if t == id {
                        Some(func)
                    } else {
                        None
                    }
                }
                _ => None,
            })
            .collect::<Vec<_>>();
        self.src
            .push_str(&format!("class {}(Protocol):\n", cls_name));
        self.src.indent();
        for method in &methods {
            self.print_sig(method, false);
            self.src.push_str(": ...\n");
        }
        if methods.is_empty() {
            self.src.push_str("pass\n\n");
        } else {
            self.src.push_str("\n\n");
        }
        self.src.dedent();
    }

    fn import_shared_type(&mut self, ty: &str) {
        let path = if self.at_root { ".types" } else { "..types" };
        self.src.pyimport(path, ty);
    }

    fn name_of(&mut self, ty: &str) -> String {
        let ty = ty.to_upper_camel_case().escape();
        if !self.at_root {
            return ty;
        }
        let id = self.interface.unwrap();
        let (module, iface) = match self.gen.imported_interfaces.get(&id) {
            Some(name) => (".imports", name),
            None => (".exports", self.gen.exported_interfaces.get(&id).unwrap()),
        };
        let iface = iface.to_snake_case().escape();
        self.src.pyimport(&module, iface.as_str());
        format!("{iface}.{ty}")
    }

    fn fqn_name(&mut self, name: &str, type_id: &TypeId) -> String {
        let ty = &self.resolve.types[*type_id];
        if let Some(name) = &ty.name {
            let owner = match ty.owner {
                TypeOwner::Interface(id) => id,
                _ => unreachable!(),
            };
            if Some(owner) != self.interface {
                let iface = match self.gen.imported_interfaces.get(&owner) {
                    Some(name) => name,
                    None => &self.gen.exported_interfaces[&owner],
                };
                return format!(
                    "{}.{}",
                    iface.to_snake_case().escape(),
                    name.to_upper_camel_case().escape()
                );
            }
        };
        self.name_of(name).to_string()
    }
}

struct FunctionBindgen<'a, 'b> {
    gen: &'a mut InterfaceGenerator<'b>,
    locals: Ns,
    block_storage: Vec<source::Body>,
    blocks: Vec<(String, Vec<String>)>,
    params: Vec<String>,
    payloads: Vec<String>,

    memory: Option<String>,
    realloc: Option<String>,
    post_return: Option<String>,
    callee: String,
    resource_map: Option<&'a ResourceMap>,
}

impl FunctionBindgen<'_, '_> {
    fn clamp<T>(&mut self, results: &mut Vec<String>, operands: &[String], min: T, max: T)
    where
        T: std::fmt::Display,
    {
        let clamp = self.print_clamp();
        results.push(format!("{clamp}({}, {min}, {max})", operands[0]));
    }

    fn load(&mut self, ty: &str, offset: i32, operands: &[String], results: &mut Vec<String>) {
        let load = self.print_load();
        let memory = self.memory.as_ref().unwrap();
        let tmp = self.locals.tmp("load");
        self.gen.src.pyimport("ctypes", None);
        uwriteln!(
            self.gen.src,
            "{tmp} = {load}(ctypes.{ty}, {memory}, caller, {}, {offset})",
            operands[0],
        );
        results.push(tmp);
    }

    fn store(&mut self, ty: &str, offset: i32, operands: &[String]) {
        let store = self.print_store();
        let memory = self.memory.as_ref().unwrap();
        self.gen.src.pyimport("ctypes", None);
        uwriteln!(
            self.gen.src,
            "{store}(ctypes.{ty}, {memory}, caller, {}, {offset}, {})",
            operands[1],
            operands[0]
        );
    }

    fn print_ty(&mut self, ty: &Type) {
        self.gen.print_ty(ty, false)
    }

    fn print_list(&mut self, element: &Type) {
        self.gen.print_list(element)
    }

    fn print_intrinsic(
        &mut self,
        name: &'static str,
        gen: impl FnOnce(&str, &mut Source),
    ) -> &'static str {
        let path = if self.gen.at_root {
            ".intrinsics"
        } else {
            "..intrinsics"
        };
        self.gen.src.pyimport(path, name);
        if !self.gen.gen.all_intrinsics.insert(name) {
            return name;
        }
        gen(name, &mut self.gen.gen.intrinsics);
        return name;
    }

    fn print_validate_guest_char(&mut self) -> &'static str {
        self.print_intrinsic("_validate_guest_char", |name, src| {
            uwriteln!(
                src,
                "
                    def {name}(i: int) -> str:
                        if i > 0x10ffff or (i >= 0xd800 and i <= 0xdfff):
                            raise TypeError('not a valid char')
                        return chr(i)
                ",
            );
        })
    }

    fn print_i32_to_f32(&mut self) -> &'static str {
        self.print_i32_to_f32_cvts();
        self.print_intrinsic("_i32_to_f32", |name, src| {
            uwriteln!(
                src,
                "
                    def {name}(i: int) -> float:
                        _i32_to_f32_i32[0] = i
                        return _i32_to_f32_f32[0]
                ",
            );
        })
    }

    fn print_f32_to_i32(&mut self) -> &'static str {
        self.print_i32_to_f32_cvts();
        self.print_intrinsic("_f32_to_i32", |name, src| {
            uwriteln!(
                src,
                "
                    def {name}(i: float) -> int:
                        _i32_to_f32_f32[0] = i
                        return _i32_to_f32_i32[0]
                ",
            );
        })
    }

    fn print_i32_to_f32_cvts(&mut self) {
        if !self.gen.gen.all_intrinsics.insert("i32_to_f32_cvts") {
            return;
        }
        self.gen.gen.intrinsics.pyimport("ctypes", None);
        self.gen
            .gen
            .intrinsics
            .push_str("_i32_to_f32_i32 = ctypes.pointer(ctypes.c_int32(0))\n");
        self.gen.gen.intrinsics.push_str(
            "_i32_to_f32_f32 = ctypes.cast(_i32_to_f32_i32, ctypes.POINTER(ctypes.c_float))\n",
        );
    }

    fn print_i64_to_f64(&mut self) -> &'static str {
        self.print_i64_to_f64_cvts();
        self.print_intrinsic("_i64_to_f64", |name, src| {
            uwriteln!(
                src,
                "
                    def {name}(i: int) -> float:
                        _i64_to_f64_i64[0] = i
                        return _i64_to_f64_f64[0]
                ",
            );
        })
    }

    fn print_f64_to_i64(&mut self) -> &'static str {
        self.print_i64_to_f64_cvts();
        self.print_intrinsic("_f64_to_i64", |name, src| {
            uwriteln!(
                src,
                "
                    def {name}(i: float) -> int:
                        _i64_to_f64_f64[0] = i
                        return _i64_to_f64_i64[0]
                ",
            );
        })
    }

    fn print_i64_to_f64_cvts(&mut self) {
        if !self.gen.gen.all_intrinsics.insert("i64_to_f64_cvts") {
            return;
        }
        self.gen.gen.intrinsics.pyimport("ctypes", None);
        self.gen
            .gen
            .intrinsics
            .push_str("_i64_to_f64_i64 = ctypes.pointer(ctypes.c_int64(0))\n");
        self.gen.gen.intrinsics.push_str(
            "_i64_to_f64_f64 = ctypes.cast(_i64_to_f64_i64, ctypes.POINTER(ctypes.c_double))\n",
        );
    }

    fn print_clamp(&mut self) -> &'static str {
        self.print_intrinsic("_clamp", |name, src| {
            uwriteln!(
                src,
                "
                    def {name}(i: int, min: int, max: int) -> int:
                        if i < min or i > max:
                            raise OverflowError(f'must be between {{min}} and {{max}}')
                        return i
                ",
            );
        })
    }

    fn print_load(&mut self) -> &'static str {
        self.print_intrinsic("_load", |name, src| {
            src.pyimport("wasmtime", None);
            src.pyimport("ctypes", None);
            src.pyimport("typing", "Any");
            uwriteln!(
                src,
                "
                    def {name}(ty: Any, mem: wasmtime.Memory, store: wasmtime.Storelike, base: int, offset: int) -> Any:
                        ptr = (base & 0xffffffff) + offset
                        if ptr + ctypes.sizeof(ty) > mem.data_len(store):
                            raise IndexError('out-of-bounds store')
                        raw_base = mem.data_ptr(store)
                        c_ptr = ctypes.POINTER(ty)(
                            ty.from_address(ctypes.addressof(raw_base.contents) + ptr)
                        )
                        return c_ptr[0]
                ",
            );
        })
    }

    fn print_store(&mut self) -> &'static str {
        self.print_intrinsic("_store", |name, src| {
            src.pyimport("wasmtime", None);
            src.pyimport("ctypes", None);
            src.pyimport("typing", "Any");
            uwriteln!(
                src,
                "
                    def {name}(ty: Any, mem: wasmtime.Memory, store: wasmtime.Storelike, base: int, offset: int, val: Any) -> None:
                        ptr = (base & 0xffffffff) + offset
                        if ptr + ctypes.sizeof(ty) > mem.data_len(store):
                            raise IndexError('out-of-bounds store')
                        raw_base = mem.data_ptr(store)
                        c_ptr = ctypes.POINTER(ty)(
                            ty.from_address(ctypes.addressof(raw_base.contents) + ptr)
                        )
                        c_ptr[0] = val
                ",
            );
        })
    }

    fn print_decode_utf8(&mut self) -> &'static str {
        self.print_intrinsic("_decode_utf8", |name, src| {
            src.pyimport("wasmtime", None);
            src.pyimport("ctypes", None);
            src.pyimport("typing", "Tuple");
            uwriteln!(
                src,
                "
                    def {name}(mem: wasmtime.Memory, store: wasmtime.Storelike, ptr: int, len: int) -> str:
                        ptr = ptr & 0xffffffff
                        len = len & 0xffffffff
                        if ptr + len > mem.data_len(store):
                            raise IndexError('string out of bounds')
                        base = mem.data_ptr(store)
                        base = ctypes.POINTER(ctypes.c_ubyte)(
                            ctypes.c_ubyte.from_address(ctypes.addressof(base.contents) + ptr)
                        )
                        return ctypes.string_at(base, len).decode('utf-8')
                ",
            );
        })
    }

    fn print_encode_utf8(&mut self) -> &'static str {
        self.print_intrinsic("_encode_utf8", |name, src| {
            src.pyimport("wasmtime", None);
            src.pyimport("ctypes", None);
            src.pyimport("typing", "Tuple");
            uwriteln!(
                src,
                "
                    def {name}(val: str, realloc: wasmtime.Func, mem: wasmtime.Memory, store: wasmtime.Storelike) -> Tuple[int, int]:
                        bytes = val.encode('utf8')
                        ptr = realloc(store, 0, 0, 1, len(bytes))
                        assert(isinstance(ptr, int))
                        ptr = ptr & 0xffffffff
                        if ptr + len(bytes) > mem.data_len(store):
                            raise IndexError('string out of bounds')
                        base = mem.data_ptr(store)
                        base = ctypes.POINTER(ctypes.c_ubyte)(
                            ctypes.c_ubyte.from_address(ctypes.addressof(base.contents) + ptr)
                        )
                        ctypes.memmove(base, bytes, len(bytes))
                        return (ptr, len(bytes))
                ",
            );
        })
    }

    fn print_canon_lift(&mut self) -> &'static str {
        self.print_intrinsic("_list_canon_lift", |name, src| {
            src.pyimport("wasmtime", None);
            src.pyimport("ctypes", None);
            src.pyimport("typing", "List");
            src.pyimport("typing", "Any");
            // TODO: this is doing a native-endian read, not a little-endian
            // read
            uwriteln!(
                src,
                "
                    def {name}(ptr: int, len: int, size: int, ty: Any, mem: wasmtime.Memory ,store: wasmtime.Storelike) -> Any:
                        ptr = ptr & 0xffffffff
                        len = len & 0xffffffff
                        if ptr + len * size > mem.data_len(store):
                            raise IndexError('list out of bounds')
                        raw_base = mem.data_ptr(store)
                        base = ctypes.POINTER(ty)(
                            ty.from_address(ctypes.addressof(raw_base.contents) + ptr)
                        )
                        if ty == ctypes.c_uint8:
                            return ctypes.string_at(base, len)
                        return base[:len]
                ",
            );
        })
    }

    fn print_canon_lower(&mut self) -> &'static str {
        self.print_intrinsic("_list_canon_lower", |name, src| {
            src.pyimport("wasmtime", None);
            src.pyimport("ctypes", None);
            src.pyimport("typing", "Tuple");
            src.pyimport("typing", "List");
            src.pyimport("typing", "Any");
            // TODO: is there a faster way to memcpy other than iterating over
            // the input list?
            // TODO: this is doing a native-endian write, not a little-endian
            // write
            uwriteln!(
                src,
                "
                    def {name}(list: Any, ty: Any, size: int, align: int, realloc: wasmtime.Func, mem: wasmtime.Memory, store: wasmtime.Storelike) -> Tuple[int, int]:
                        total_size = size * len(list)
                        ptr = realloc(store, 0, 0, align, total_size)
                        assert(isinstance(ptr, int))
                        ptr = ptr & 0xffffffff
                        if ptr + total_size > mem.data_len(store):
                            raise IndexError('list realloc return of bounds')
                        raw_base = mem.data_ptr(store)
                        base = ctypes.POINTER(ty)(
                            ty.from_address(ctypes.addressof(raw_base.contents) + ptr)
                        )
                        for i, val in enumerate(list):
                            base[i] = val
                        return (ptr, len(list))
                ",
            );
        })
    }

    fn name_of(&mut self, ty: &str) -> String {
        self.gen.name_of(ty)
    }

    fn bitcast(&mut self, cast: &Bitcast, op: &str) -> String {
        match cast {
            Bitcast::I32ToF32 => {
                let cvt = self.print_i32_to_f32();
                format!("{cvt}({})", op)
            }
            Bitcast::F32ToI32 => {
                let cvt = self.print_f32_to_i32();
                format!("{cvt}({})", op)
            }
            Bitcast::I64ToF64 => {
                let cvt = self.print_i64_to_f64();
                format!("{cvt}({})", op)
            }
            Bitcast::F64ToI64 => {
                let cvt = self.print_f64_to_i64();
                format!("{cvt}({})", op)
            }
            Bitcast::I64ToF32 => {
                let cvt = self.print_i32_to_f32();
                format!("{cvt}(({}) & 0xffffffff)", op)
            }
            Bitcast::F32ToI64 => {
                let cvt = self.print_f32_to_i32();
                format!("{cvt}({})", op)
            }
            Bitcast::I32ToI64
            | Bitcast::I64ToI32
            | Bitcast::None
            | Bitcast::P64ToI64
            | Bitcast::I64ToP64
            | Bitcast::P64ToP
            | Bitcast::PToP64
            | Bitcast::I32ToP
            | Bitcast::PToI32
            | Bitcast::PToL
            | Bitcast::LToP
            | Bitcast::I32ToL
            | Bitcast::LToI32
            | Bitcast::I64ToL
            | Bitcast::LToI64 => op.to_string(),
            Bitcast::Sequence(seq) => {
                let [a, b] = &**seq;
                let a = self.bitcast(a, op);
                self.bitcast(b, &a)
            }
        }
    }
}

impl Bindgen for FunctionBindgen<'_, '_> {
    type Operand = String;

    fn sizes(&self) -> &SizeAlign {
        &self.gen.gen.sizes
    }

    fn push_block(&mut self) {
        self.block_storage.push(self.gen.src.take_body());
    }

    fn finish_block(&mut self, operands: &mut Vec<String>) {
        let to_restore = self.block_storage.pop().unwrap();
        let src = self.gen.src.replace_body(to_restore);
        self.blocks.push((src, mem::take(operands)));
    }

    fn return_pointer(&mut self, _size: usize, _align: usize) -> String {
        unimplemented!()
    }

    fn is_list_canonical(&self, resolve: &Resolve, ty: &Type) -> bool {
        array_ty(resolve, ty).is_some()
    }

    fn emit(
        &mut self,
        resolve: &Resolve,
        inst: &Instruction<'_>,
        operands: &mut Vec<String>,
        results: &mut Vec<String>,
    ) {
        match inst {
            Instruction::GetArg { nth } => results.push(self.params[*nth].clone()),
            Instruction::I32Const { val } => results.push(val.to_string()),
            Instruction::ConstZero { tys } => {
                for t in tys.iter() {
                    match t {
                        WasmType::I32
                        | WasmType::I64
                        | WasmType::Length
                        | WasmType::Pointer
                        | WasmType::PointerOrI64 => results.push("0".to_string()),
                        WasmType::F32 | WasmType::F64 => results.push("0.0".to_string()),
                    }
                }
            }

            // The representation of i32 in Python is a number, so 8/16-bit
            // values get further clamped to ensure that the upper bits aren't
            // set when we pass the value, ensuring that only the right number
            // of bits are transferred.
            Instruction::U8FromI32 => self.clamp(results, operands, u8::MIN, u8::MAX),
            Instruction::S8FromI32 => self.clamp(results, operands, i8::MIN, i8::MAX),
            Instruction::U16FromI32 => self.clamp(results, operands, u16::MIN, u16::MAX),
            Instruction::S16FromI32 => self.clamp(results, operands, i16::MIN, i16::MAX),
            // Ensure the bits of the number are treated as unsigned.
            Instruction::U32FromI32 => {
                results.push(format!("{} & 0xffffffff", operands[0]));
            }
            // All bigints coming from wasm are treated as signed, so convert
            // it to ensure it's treated as unsigned.
            Instruction::U64FromI64 => {
                results.push(format!("{} & 0xffffffffffffffff", operands[0]));
            }
            // Nothing to do signed->signed where the representations are the
            // same.
            Instruction::S32FromI32 | Instruction::S64FromI64 => {
                results.push(operands.pop().unwrap())
            }

            // All values coming from the host and going to wasm need to have
            // their ranges validated, since the host could give us any value.
            Instruction::I32FromU8 => self.clamp(results, operands, u8::MIN, u8::MAX),
            Instruction::I32FromS8 => self.clamp(results, operands, i8::MIN, i8::MAX),
            Instruction::I32FromU16 => self.clamp(results, operands, u16::MIN, u16::MAX),
            Instruction::I32FromS16 => self.clamp(results, operands, i16::MIN, i16::MAX),
            // TODO: need to do something to get this to be represented as signed?
            Instruction::I32FromU32 => {
                self.clamp(results, operands, u32::MIN, u32::MAX);
            }
            Instruction::I32FromS32 => self.clamp(results, operands, i32::MIN, i32::MAX),
            // TODO: need to do something to get this to be represented as signed?
            Instruction::I64FromU64 => self.clamp(results, operands, u64::MIN, u64::MAX),
            Instruction::I64FromS64 => self.clamp(results, operands, i64::MIN, i64::MAX),

            // Python uses `float` for f32/f64, so everything is equivalent
            // here.
            Instruction::CoreF32FromF32
            | Instruction::CoreF64FromF64
            | Instruction::F32FromCoreF32
            | Instruction::F64FromCoreF64 => results.push(operands.pop().unwrap()),

            // Validate that i32 values coming from wasm are indeed valid code
            // points.
            Instruction::CharFromI32 => {
                let validate = self.print_validate_guest_char();
                results.push(format!("{validate}({})", operands[0]));
            }

            Instruction::I32FromChar => {
                results.push(format!("ord({})", operands[0]));
            }

            Instruction::Bitcasts { casts } => {
                for (cast, op) in casts.iter().zip(operands) {
                    results.push(self.bitcast(cast, op));
                }
            }

            Instruction::BoolFromI32 => {
                let op = self.locals.tmp("operand");
                let ret = self.locals.tmp("boolean");

                uwriteln!(self.gen.src, "{op} = {}", operands[0]);
                uwriteln!(self.gen.src, "if {op} == 0:");
                self.gen.src.indent();
                uwriteln!(self.gen.src, "{ret} = False");
                self.gen.src.dedent();
                uwriteln!(self.gen.src, "elif {op} == 1:");
                self.gen.src.indent();
                uwriteln!(self.gen.src, "{ret} = True");
                self.gen.src.dedent();
                uwriteln!(self.gen.src, "else:");
                self.gen.src.indent();
                uwriteln!(
                    self.gen.src,
                    "raise TypeError(\"invalid variant discriminant for bool\")"
                );
                self.gen.src.dedent();
                results.push(ret);
            }
            Instruction::I32FromBool => {
                results.push(format!("int({})", operands[0]));
            }

            Instruction::RecordLower { record, .. } => {
                if record.fields.is_empty() {
                    return;
                }
                let tmp = self.locals.tmp("record");
                uwriteln!(self.gen.src, "{tmp} = {}", operands[0]);
                for field in record.fields.iter() {
                    let name = self.locals.tmp("field");
                    uwriteln!(
                        self.gen.src,
                        "{name} = {tmp}.{}",
                        field.name.to_snake_case().escape(),
                    );
                    results.push(name);
                }
            }

            Instruction::RecordLift { name, ty, .. } => {
                let fqn_name = &self.gen.fqn_name(name, ty);
                results.push(format!("{}({})", fqn_name, operands.join(", ")));
            }
            Instruction::TupleLower { tuple, .. } => {
                if tuple.types.is_empty() {
                    return;
                }
                self.gen.src.push_str("(");
                for _ in 0..tuple.types.len() {
                    let name = self.locals.tmp("tuplei");
                    uwrite!(self.gen.src, "{name},");
                    results.push(name);
                }
                uwriteln!(self.gen.src, ") = {}", operands[0]);
            }
            Instruction::TupleLift { .. } => {
                if operands.is_empty() {
                    results.push("None".to_string());
                } else {
                    results.push(format!("({},)", operands.join(", ")));
                }
            }
            Instruction::FlagsLift { name, .. } => {
                let operand = match operands.len() {
                    1 => operands[0].clone(),
                    _ => {
                        let tmp = self.locals.tmp("bits");
                        uwriteln!(self.gen.src, "{tmp} = 0");
                        for (i, op) in operands.iter().enumerate() {
                            let i = 32 * i;
                            uwriteln!(self.gen.src, "{tmp} |= ({op} & 0xffffffff) << {i}\n");
                        }
                        tmp
                    }
                };
                results.push(format!("{}({operand})", self.name_of(name)));
            }
            Instruction::FlagsLower { flags, .. } => match flags.repr().count() {
                1 => results.push(format!("({}).value", operands[0])),
                n => {
                    let tmp = self.locals.tmp("bits");
                    self.gen
                        .src
                        .push_str(&format!("{tmp} = ({}).value\n", operands[0]));
                    for i in 0..n {
                        let i = 32 * i;
                        results.push(format!("({tmp} >> {i}) & 0xffffffff"));
                    }
                }
            },

            Instruction::VariantPayloadName => {
                let name = self.locals.tmp("payload");
                results.push(name.clone());
                self.payloads.push(name);
            }

            Instruction::VariantLower {
                variant,
                results: result_types,
                name,
                ty,
                ..
            } => {
                let blocks = self
                    .blocks
                    .drain(self.blocks.len() - variant.cases.len()..)
                    .collect::<Vec<_>>();
                let payloads = self
                    .payloads
                    .drain(self.payloads.len() - variant.cases.len()..)
                    .collect::<Vec<_>>();

                for _ in 0..result_types.len() {
                    results.push(self.locals.tmp("variant"));
                }

                for (i, ((case, (block, block_results)), payload)) in
                    variant.cases.iter().zip(blocks).zip(payloads).enumerate()
                {
                    if i == 0 {
                        self.gen.src.push_str("if ");
                    } else {
                        self.gen.src.push_str("elif ");
                    }
                    uwrite!(self.gen.src, "isinstance({}, ", operands[0]);
                    self.print_ty(&Type::Id(*ty));
                    uwriteln!(
                        self.gen.src,
                        "{}):",
                        case.name.to_upper_camel_case().escape()
                    );

                    self.gen.src.indent();
                    if case.ty.is_some() {
                        uwriteln!(self.gen.src, "{payload} = {}.value", operands[0]);
                    }
                    self.gen.src.push_str(&block);

                    for (i, result) in block_results.iter().enumerate() {
                        uwriteln!(self.gen.src, "{} = {result}", results[i]);
                    }
                    self.gen.src.dedent();
                }
                let variant_name = name.to_upper_camel_case().escape();
                self.gen.src.push_str("else:\n");
                self.gen.src.indent();
                uwriteln!(
                    self.gen.src,
                    "raise TypeError(\"invalid variant specified for {variant_name}\")",
                );
                self.gen.src.dedent();
            }

            Instruction::VariantLift {
                variant, name, ty, ..
            } => {
                let blocks = self
                    .blocks
                    .drain(self.blocks.len() - variant.cases.len()..)
                    .collect::<Vec<_>>();

                let result = self.locals.tmp("variant");
                uwrite!(self.gen.src, "{result}: ");
                self.print_ty(&Type::Id(*ty));
                self.gen.src.push_str("\n");
                for (i, (case, (block, block_results))) in
                    variant.cases.iter().zip(blocks).enumerate()
                {
                    if i == 0 {
                        self.gen.src.push_str("if ");
                    } else {
                        self.gen.src.push_str("elif ");
                    }
                    uwriteln!(self.gen.src, "{} == {i}:", operands[0]);
                    self.gen.src.indent();
                    self.gen.src.push_str(&block);

                    uwrite!(self.gen.src, "{result} = ");
                    self.print_ty(&Type::Id(*ty));
                    uwrite!(
                        self.gen.src,
                        "{}(",
                        case.name.to_upper_camel_case().escape()
                    );
                    if block_results.len() > 0 {
                        assert!(block_results.len() == 1);
                        self.gen.src.push_str(&block_results[0]);
                    }
                    self.gen.src.push_str(")\n");
                    self.gen.src.dedent();
                }
                self.gen.src.push_str("else:\n");
                self.gen.src.indent();
                let variant_name = name.to_upper_camel_case().escape();
                uwriteln!(
                    self.gen.src,
                    "raise TypeError(\"invalid variant discriminant for {variant_name}\")",
                );
                self.gen.src.dedent();
                results.push(result);
            }

            Instruction::OptionLower {
                results: result_types,
                ty,
                ..
            } => {
                let TypeDefKind::Option(some_type) = &self.gen.resolve.types[*ty].kind else {
                    unreachable!()
                };
                let nesting = is_option(self.gen.resolve, *some_type);
                if nesting {
                    self.gen.import_shared_type("Some");
                }

                let (some, some_results) = self.blocks.pop().unwrap();
                let (none, none_results) = self.blocks.pop().unwrap();
                let some_payload = self.payloads.pop().unwrap();
                let _none_payload = self.payloads.pop().unwrap();

                for _ in 0..result_types.len() {
                    results.push(self.locals.tmp("variant"));
                }

                let op0 = &operands[0];
                uwriteln!(self.gen.src, "if {op0} is None:");

                self.gen.src.indent();
                self.gen.src.push_str(&none);
                for (dst, result) in results.iter().zip(&none_results) {
                    uwriteln!(self.gen.src, "{dst} = {result}");
                }
                self.gen.src.dedent();
                self.gen.src.push_str("else:\n");
                self.gen.src.indent();
                uwriteln!(
                    self.gen.src,
                    "{some_payload} = {op0}{}",
                    if nesting { ".value" } else { "" }
                );
                self.gen.src.push_str(&some);
                for (dst, result) in results.iter().zip(&some_results) {
                    uwriteln!(self.gen.src, "{dst} = {result}");
                }
                self.gen.src.dedent();
            }

            Instruction::OptionLift { ty, .. } => {
                let TypeDefKind::Option(some_type) = &self.gen.resolve.types[*ty].kind else {
                    unreachable!()
                };
                let nesting = is_option(self.gen.resolve, *some_type);
                if nesting {
                    self.gen.import_shared_type("Some");
                }

                let (some, some_results) = self.blocks.pop().unwrap();
                let (none, none_results) = self.blocks.pop().unwrap();
                assert!(none_results.len() == 0);
                assert!(some_results.len() == 1);
                let some_result = &some_results[0];

                let result = self.locals.tmp("option");
                uwrite!(self.gen.src, "{result}: ");
                self.print_ty(&Type::Id(*ty));
                self.gen.src.push_str("\n");

                let op0 = &operands[0];
                uwriteln!(self.gen.src, "if {op0} == 0:");
                self.gen.src.indent();
                self.gen.src.push_str(&none);
                uwriteln!(self.gen.src, "{result} = None");
                self.gen.src.dedent();
                uwriteln!(self.gen.src, "elif {op0} == 1:");
                self.gen.src.indent();
                self.gen.src.push_str(&some);
                if nesting {
                    uwriteln!(self.gen.src, "{result} = Some({some_result})");
                } else {
                    uwriteln!(self.gen.src, "{result} = {some_result}");
                }
                self.gen.src.dedent();

                self.gen.src.push_str("else:\n");
                self.gen.src.indent();
                self.gen
                    .src
                    .push_str("raise TypeError(\"invalid variant discriminant for option\")\n");
                self.gen.src.dedent();

                results.push(result);
            }

            Instruction::ResultLower {
                results: result_types,
                ..
            } => {
                let (err, err_results) = self.blocks.pop().unwrap();
                let (ok, ok_results) = self.blocks.pop().unwrap();
                let err_payload = self.payloads.pop().unwrap();
                let ok_payload = self.payloads.pop().unwrap();
                self.gen.import_shared_type("Ok");
                self.gen.import_shared_type("Err");

                for _ in 0..result_types.len() {
                    results.push(self.locals.tmp("variant"));
                }

                let op0 = &operands[0];
                uwriteln!(self.gen.src, "if isinstance({op0}, Ok):");

                self.gen.src.indent();
                uwriteln!(self.gen.src, "{ok_payload} = {op0}.value");
                self.gen.src.push_str(&ok);
                for (dst, result) in results.iter().zip(&ok_results) {
                    uwriteln!(self.gen.src, "{dst} = {result}");
                }
                self.gen.src.dedent();
                uwriteln!(self.gen.src, "elif isinstance({op0}, Err):");
                self.gen.src.indent();
                uwriteln!(self.gen.src, "{err_payload} = {op0}.value");
                self.gen.src.push_str(&err);
                for (dst, result) in results.iter().zip(&err_results) {
                    uwriteln!(self.gen.src, "{dst} = {result}");
                }
                self.gen.src.dedent();
                self.gen.src.push_str("else:\n");
                self.gen.src.indent();
                self.gen.src.push_str(&format!(
                    "raise TypeError(\"invalid variant specified for expected\")\n",
                ));
                self.gen.src.dedent();
            }

            Instruction::ResultLift { ty, .. } => {
                let (err, err_results) = self.blocks.pop().unwrap();
                let (ok, ok_results) = self.blocks.pop().unwrap();
                let none = String::from("None");
                let err_result = err_results.get(0).unwrap_or(&none);
                let ok_result = ok_results.get(0).unwrap_or(&none);

                self.gen.import_shared_type("Ok");
                self.gen.import_shared_type("Err");

                let result = self.locals.tmp("expected");
                uwrite!(self.gen.src, "{result}: ");
                self.print_ty(&Type::Id(*ty));
                self.gen.src.push_str("\n");

                let op0 = &operands[0];
                uwriteln!(self.gen.src, "if {op0} == 0:");
                self.gen.src.indent();
                self.gen.src.push_str(&ok);
                uwriteln!(self.gen.src, "{result} = Ok({ok_result})");
                self.gen.src.dedent();
                uwriteln!(self.gen.src, "elif {op0} == 1:");
                self.gen.src.indent();
                self.gen.src.push_str(&err);
                uwriteln!(self.gen.src, "{result} = Err({err_result})");
                self.gen.src.dedent();

                self.gen.src.push_str("else:\n");
                self.gen.src.indent();
                self.gen
                    .src
                    .push_str("raise TypeError(\"invalid variant discriminant for expected\")\n");
                self.gen.src.dedent();

                results.push(result);
            }

            Instruction::EnumLower { .. } => results.push(format!("({}).value", operands[0])),

            Instruction::EnumLift { name, ty, .. } => {
                let fqn_name = &self.gen.fqn_name(name, ty);
                results.push(format!("{}({})", fqn_name, operands[0]));
            }

            Instruction::ListCanonLower { element, .. } => {
                let lower = self.print_canon_lower();
                let realloc = self.realloc.as_ref().unwrap();
                let memory = self.memory.as_ref().unwrap();

                let ptr = self.locals.tmp("ptr");
                let len = self.locals.tmp("len");
                let array_ty = array_ty(resolve, element).unwrap();
                let size = self.gen.gen.sizes.size(element).size_wasm32();
                let align = self.gen.gen.sizes.align(element).align_wasm32();
                uwriteln!(
                    self.gen.src,
                    "{ptr}, {len} = {lower}({}, ctypes.{array_ty}, {size}, {align}, {realloc}, {memory}, caller)",
                    operands[0],
                );
                results.push(ptr);
                results.push(len);
            }
            Instruction::ListCanonLift { element, .. } => {
                let lift = self.print_canon_lift();
                let memory = self.memory.as_ref().unwrap();
                let ptr = self.locals.tmp("ptr");
                let len = self.locals.tmp("len");
                uwriteln!(self.gen.src, "{ptr} = {}", operands[0]);
                uwriteln!(self.gen.src, "{len} = {}", operands[1]);
                let array_ty = array_ty(resolve, element).unwrap();
                self.gen.src.pyimport("ctypes", None);
                let lift = format!(
                    "{lift}({ptr}, {len}, {}, ctypes.{array_ty}, {memory}, caller)",
                    self.gen.gen.sizes.size(element).size_wasm32(),
                );
                self.gen.src.pyimport("typing", "cast");
                let list = self.locals.tmp("list");
                uwrite!(self.gen.src, "{list} = cast(");
                self.print_list(element);
                uwriteln!(self.gen.src, ", {lift})");
                results.push(list);
            }
            Instruction::StringLower { .. } => {
                let encode = self.print_encode_utf8();
                let realloc = self.realloc.as_ref().unwrap();
                let memory = self.memory.as_ref().unwrap();

                let ptr = self.locals.tmp("ptr");
                let len = self.locals.tmp("len");
                uwriteln!(
                    self.gen.src,
                    "{ptr}, {len} = {encode}({}, {realloc}, {memory}, caller)",
                    operands[0],
                );
                results.push(ptr);
                results.push(len);
            }
            Instruction::StringLift => {
                let decode = self.print_decode_utf8();
                let memory = self.memory.as_ref().unwrap();
                let ptr = self.locals.tmp("ptr");
                let len = self.locals.tmp("len");
                uwriteln!(self.gen.src, "{ptr} = {}", operands[0]);
                uwriteln!(self.gen.src, "{len} = {}", operands[1]);
                let list = self.locals.tmp("list");
                uwriteln!(
                    self.gen.src,
                    "{list} = {decode}({memory}, caller, {ptr}, {len})"
                );
                results.push(list);
            }

            Instruction::ListLower { element, .. } => {
                let base = self.payloads.pop().unwrap();
                let e = self.payloads.pop().unwrap();
                let realloc = self.realloc.as_ref().unwrap();
                let (body, body_results) = self.blocks.pop().unwrap();
                assert!(body_results.is_empty());
                let vec = self.locals.tmp("vec");
                let result = self.locals.tmp("result");
                let len = self.locals.tmp("len");
                let size = self.gen.gen.sizes.size(element).size_wasm32();
                let align = self.gen.gen.sizes.align(element).align_wasm32();

                // first store our vec-to-lower in a temporary since we'll
                // reference it multiple times.
                uwriteln!(self.gen.src, "{vec} = {}", operands[0]);
                uwriteln!(self.gen.src, "{len} = len({vec})");

                // ... then realloc space for the result in the guest module
                uwriteln!(
                    self.gen.src,
                    "{result} = {realloc}(caller, 0, 0, {align}, {len} * {size})",
                );
                uwriteln!(self.gen.src, "assert(isinstance({result}, int))");

                // ... then consume the vector and use the block to lower the
                // result.
                let i = self.locals.tmp("i");
                uwriteln!(self.gen.src, "for {i} in range(0, {len}):");
                self.gen.src.indent();
                uwriteln!(self.gen.src, "{e} = {vec}[{i}]");
                uwriteln!(self.gen.src, "{base} = {result} + {i} * {size}");
                self.gen.src.push_str(&body);
                self.gen.src.dedent();

                results.push(result);
                results.push(len);
            }

            Instruction::ListLift { element, .. } => {
                let (body, body_results) = self.blocks.pop().unwrap();
                let base = self.payloads.pop().unwrap();
                let size = self.gen.gen.sizes.size(element).size_wasm32();
                let ptr = self.locals.tmp("ptr");
                let len = self.locals.tmp("len");
                uwriteln!(self.gen.src, "{ptr} = {}", operands[0]);
                uwriteln!(self.gen.src, "{len} = {}", operands[1]);
                let result = self.locals.tmp("result");
                uwrite!(self.gen.src, "{result}: ");
                self.print_list(element);
                uwriteln!(self.gen.src, " = []");

                let i = self.locals.tmp("i");
                assert_eq!(body_results.len(), 1);
                let body_result0 = &body_results[0];

                uwriteln!(self.gen.src, "for {i} in range(0, {len}):");
                self.gen.src.indent();
                uwriteln!(self.gen.src, "{base} = {ptr} + {i} * {size}");
                self.gen.src.push_str(&body);
                uwriteln!(self.gen.src, "{result}.append({body_result0})");
                self.gen.src.dedent();
                results.push(result);
            }

            Instruction::IterElem { .. } => {
                let name = self.locals.tmp("e");
                results.push(name.clone());
                self.payloads.push(name);
            }
            Instruction::IterBasePointer => {
                let name = self.locals.tmp("base");
                results.push(name.clone());
                self.payloads.push(name);
            }
            Instruction::CallWasm { sig, .. } => {
                if sig.results.len() > 0 {
                    for i in 0..sig.results.len() {
                        if i > 0 {
                            self.gen.src.push_str(", ");
                        }
                        let ret = self.locals.tmp("ret");
                        self.gen.src.push_str(&ret);
                        results.push(ret);
                    }
                    self.gen.src.push_str(" = ");
                }
                self.gen.src.push_str(&self.callee);
                self.gen.src.push_str("(caller");
                if operands.len() > 0 {
                    self.gen.src.push_str(", ");
                }
                self.gen.src.push_str(&operands.join(", "));
                self.gen.src.push_str(")\n");
                for (ty, name) in sig.results.iter().zip(results.iter()) {
                    let ty = wasm_ty_typing(*ty);
                    self.gen
                        .src
                        .push_str(&format!("assert(isinstance({}, {}))\n", name, ty));
                }
            }
            Instruction::CallInterface { func, async_ } => {
                assert!(!async_);
                for i in 0..func.results.len() {
                    if i > 0 {
                        self.gen.src.push_str(", ");
                    }
                    let result = self.locals.tmp("ret");
                    self.gen.src.push_str(&result);
                    results.push(result);
                }
                if func.results.len() > 0 {
                    self.gen.src.push_str(" = ");
                }
                match &func.kind {
                    FunctionKind::Freestanding => {
                        self.gen
                            .src
                            .push_str(&format!("{}({})", self.callee, operands.join(", "),));
                    }
                    FunctionKind::Method(_)
                    | FunctionKind::Static(_)
                    | FunctionKind::Constructor(_) => {
                        unimplemented!()
                    }
                }
                self.gen.src.push_str("\n");
            }

            Instruction::Return { amt, func } => {
                if let Some(s) = &self.post_return {
                    self.gen.src.push_str(&format!("{s}(caller, ret)\n"));
                }
                match func.kind {
                    FunctionKind::Constructor(_) => {} // No return value for __init__
                    _ => match amt {
                        0 => {}
                        1 => self.gen.src.push_str(&format!("return {}\n", operands[0])),
                        _ => {
                            self.gen
                                .src
                                .push_str(&format!("return ({})\n", operands.join(", ")));
                        }
                    },
                }
            }

            Instruction::I32Load { offset }
            | Instruction::LengthLoad { offset }
            | Instruction::PointerLoad { offset } => {
                self.load("c_int32", *offset, operands, results)
            }
            Instruction::I64Load { offset } => self.load("c_int64", *offset, operands, results),
            Instruction::F32Load { offset } => self.load("c_float", *offset, operands, results),
            Instruction::F64Load { offset } => self.load("c_double", *offset, operands, results),
            Instruction::I32Load8U { offset } => self.load("c_uint8", *offset, operands, results),
            Instruction::I32Load8S { offset } => self.load("c_int8", *offset, operands, results),
            Instruction::I32Load16U { offset } => self.load("c_uint16", *offset, operands, results),
            Instruction::I32Load16S { offset } => self.load("c_int16", *offset, operands, results),
            Instruction::I32Store { offset }
            | Instruction::LengthStore { offset }
            | Instruction::PointerStore { offset } => self.store("c_uint32", *offset, operands),
            Instruction::I64Store { offset } => self.store("c_uint64", *offset, operands),
            Instruction::F32Store { offset } => self.store("c_float", *offset, operands),
            Instruction::F64Store { offset } => self.store("c_double", *offset, operands),
            Instruction::I32Store8 { offset } => self.store("c_uint8", *offset, operands),
            Instruction::I32Store16 { offset } => self.store("c_uint16", *offset, operands),

            Instruction::Malloc { size, align, .. } => {
                let realloc = self.realloc.as_ref().unwrap();
                let ptr = self.locals.tmp("ptr");
                uwriteln!(
                    self.gen.src,
                    "{ptr} = {realloc}(caller, 0, 0, {align}, {size})"
                );
                uwriteln!(self.gen.src, "assert(isinstance({ptr}, int))");
                results.push(ptr);
            }
            Instruction::HandleLift { handle, .. } => {
                let resource_map = match self.resource_map {
                    Some(resource_map) => resource_map,
                    None => unimplemented!("imported resources not yet supported"),
                };
                let (Handle::Own(ty) | Handle::Borrow(ty)) = handle;
                let resource_ty = &dealias(self.gen.resolve, *ty);
                let ResourceTable { data, .. } = &resource_map[resource_ty];
                let ResourceData::Host { tid, .. } = data;
                let table_id = tid.as_u32();
                let handle_remove = &format!("_handle_remove_{table_id}");
                uwriteln!(self.gen.src, "entry = self.component.{handle_remove}(ret)");
                uwriteln!(self.gen.src, "self._rep = entry[0]");
                return results.push("".to_string());
            }
            Instruction::HandleLower { .. } => {
                uwriteln!(self.gen.src, "rep = self._rep");
                results.push("rep".to_string());
            }
            Instruction::Flush { amt } => {
                for i in 0..*amt {
                    let tmp = self.locals.tmp("tmp");
                    uwriteln!(self.gen.src, "{tmp} = {}", operands[i]);
                    results.push(tmp);
                }
            }

            i => unimplemented!("{:?}", i),
        }
    }
}

fn wasm_ty_ctor(ty: WasmType) -> &'static str {
    match ty {
        WasmType::I32 | WasmType::Pointer | WasmType::Length => "wasmtime.ValType.i32()",
        WasmType::I64 | WasmType::PointerOrI64 => "wasmtime.ValType.i64()",
        WasmType::F32 => "wasmtime.ValType.f32()",
        WasmType::F64 => "wasmtime.ValType.f64()",
    }
}

fn wasm_ty_typing(ty: WasmType) -> &'static str {
    match ty {
        WasmType::I32
        | WasmType::I64
        | WasmType::Pointer
        | WasmType::Length
        | WasmType::PointerOrI64 => "int",
        WasmType::F32 | WasmType::F64 => "float",
    }
}

fn is_option(resolve: &Resolve, ty: Type) -> bool {
    if let Type::Id(id) = ty {
        match &resolve.types[id].kind {
            TypeDefKind::Option(_) => true,
            TypeDefKind::Type(ty) => is_option(resolve, *ty),
            _ => false,
        }
    } else {
        false
    }
}

trait Escape: ToOwned {
    fn escape(&self) -> Self::Owned;
}

impl Escape for str {
    fn escape(&self) -> String {
        // Escape Python keywords
        // Source: https://docs.python.org/3/reference/lexical_analysis.html#keywords
        match self {
            "False" | "None" | "True" | "and" | "as" | "assert" | "async" | "await" | "break"
            | "class" | "continue" | "def" | "del" | "elif" | "else" | "except" | "finally"
            | "for" | "from" | "global" | "if" | "import" | "in" | "is" | "lambda" | "nonlocal"
            | "not" | "or" | "pass" | "raise" | "return" | "try" | "while" | "with" | "yield" => {
                format!("{self}_")
            }
            _ => self.to_owned(),
        }
    }
}
