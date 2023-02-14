/// Calls [`write!`] with the passed arguments and unwraps the result.
///
/// Useful for writing to things with infallible `Write` implementations like
/// `Source` and `String`.
///
/// [`write!`]: std::write
#[macro_export]
macro_rules! uwrite {
    ($dst:expr, $($arg:tt)*) => {
        write!($dst, $($arg)*).unwrap()
    };
}

/// Calls [`writeln!`] with the passed arguments and unwraps the result.
///
/// Useful for writing to things with infallible `Write` implementations like
/// `Source` and `String`.
///
/// [`writeln!`]: std::writeln
#[macro_export]
macro_rules! uwriteln {
    ($dst:expr, $($arg:tt)*) => {
        writeln!($dst, $($arg)*).unwrap()
    };
}

mod bindgen;
mod files;
mod imports;
mod ns;
mod source;

pub use bindgen::WasmtimePy;
pub use files::Files;

#[cfg(target_arch = "wasm32")]
mod bindings {
    wit_bindgen::generate!("bindgen" in "../bindgen.wit");

    export_wasmtime_py!(PythonBindings);

    struct PythonBindings;

    impl WasmtimePy for PythonBindings {
        fn generate(name: String, component: Vec<u8>) -> Result<Vec<(String, Vec<u8>)>, String> {
            let mut gen = crate::WasmtimePy::default();
            let mut files = Default::default();
            gen.generate(&name, &component, &mut files)
                .map_err(|e| format!("{e:?}"))?;
            Ok(files
                .iter()
                .map(|(name, bytes)| (name.to_string(), bytes.to_vec()))
                .collect())
        }
    }
}
