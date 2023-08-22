use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write;

/// Tracks all of the import and intrinsics that a given codegen
/// requires and how to generate them when needed.
#[derive(Default)]
pub struct PyImports {
    pyimports: BTreeMap<String, Option<BTreeSet<String>>>,
    typing_imports: BTreeMap<String, Option<BTreeSet<String>>>,
}

impl PyImports {
    /// Record that a Python import is required
    pub fn pyimport<'a>(&mut self, module: &str, name: impl Into<Option<&'a str>>) {
        push(&mut self.pyimports, module, name.into())
    }

    pub fn typing_import<'a>(&mut self, module: &str, name: impl Into<Option<&'a str>>) {
        push(&mut self.typing_imports, module, name.into())
    }

    pub fn merge(&mut self, imports: PyImports) {
        for (module, names) in imports.pyimports {
            if let Some(names) = names {
                for name in names {
                    self.pyimport(&module, Some(name.as_str()));
                }
            } else {
                self.pyimport(&module, None);
            }
        }

        for (module, names) in imports.typing_imports {
            if let Some(names) = names {
                for name in names {
                    self.typing_import(&module, Some(name.as_str()));
                }
            } else {
                self.typing_import(&module, None);
            }
        }
    }

    pub fn is_empty(&self) -> bool {
        self.pyimports.is_empty()
    }

    pub fn finish(&self) -> String {
        let mut result = render(&self.pyimports);

        if !self.typing_imports.is_empty() {
            result.push_str("from typing import TYPE_CHECKING\n");
            result.push_str("if TYPE_CHECKING:\n");
            for line in render(&self.typing_imports).lines() {
                if !line.is_empty() {
                    result.push_str("  ");
                    result.push_str(line);
                }
                result.push_str("\n");
            }
        }

        result
    }
}

fn push(
    imports: &mut BTreeMap<String, Option<BTreeSet<String>>>,
    module: &str,
    name: Option<&str>,
) {
    let list = imports.entry(module.to_string()).or_insert(match name {
        Some(_) => Some(BTreeSet::new()),
        None => None,
    });
    match name {
        Some(name) => {
            assert!(list.is_some());
            list.as_mut().unwrap().insert(name.to_string());
        }
        None => assert!(list.is_none()),
    }
}

fn render(imports: &BTreeMap<String, Option<BTreeSet<String>>>) -> String {
    let mut result = String::new();
    for (k, list) in imports.iter() {
        match list {
            Some(list) => {
                let list = list.iter().cloned().collect::<Vec<_>>().join(", ");
                uwriteln!(result, "from {k} import {list}");
            }
            None => uwriteln!(result, "import {k}"),
        }
    }

    if !imports.is_empty() {
        result.push_str("\n");
    }
    result
}

#[cfg(test)]
mod test {
    use std::collections::{BTreeMap, BTreeSet};

    use super::PyImports;

    #[test]
    fn test_pyimport_only_contents() {
        let mut deps = PyImports::default();
        deps.pyimport("typing", None);
        deps.pyimport("typing", None);
        assert_eq!(deps.pyimports, BTreeMap::from([("typing".into(), None)]));
    }

    #[test]
    fn test_pyimport_only_module() {
        let mut deps = PyImports::default();
        deps.pyimport("typing", "Union");
        deps.pyimport("typing", "List");
        deps.pyimport("typing", "NamedTuple");
        assert_eq!(
            deps.pyimports,
            BTreeMap::from([(
                "typing".into(),
                Some(BTreeSet::from([
                    "Union".into(),
                    "List".into(),
                    "NamedTuple".into()
                ]))
            )])
        );
    }

    #[test]
    #[should_panic]
    fn test_pyimport_conflicting() {
        let mut deps = PyImports::default();
        deps.pyimport("typing", "NamedTuple");
        deps.pyimport("typing", None);
    }
}
