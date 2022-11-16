use std::path::PathBuf;

fn main() {
    let mut args = std::env::args().skip(1);
    let component = args.next().unwrap();
    let out_dir = PathBuf::from(args.next().unwrap());

    let mut gen = bindgen::WasmtimePy::default();
    let mut files = Default::default();
    let component = std::fs::read(&component).unwrap();
    gen.generate("bindgen", &component, &mut files).unwrap();

    for (name, bytes) in files.iter() {
        let path = out_dir.join(name);
        let parent = path.parent().unwrap();
        std::fs::create_dir_all(parent).unwrap();
        std::fs::write(&path, bytes).unwrap();
    }
}
