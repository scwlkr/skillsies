use crate::classify::alias;
use serde::Serialize;
use std::collections::HashMap;
use std::path::{Path, PathBuf};

#[derive(Serialize)]
pub struct StorageCategory {
    pub category: String,
    pub allocated_bytes: u64,
}

pub struct Storage {
    prefixes: Vec<(PathBuf, &'static str)>,
    totals: HashMap<&'static str, u64>,
}

impl Storage {
    pub fn new(home: &Path) -> Self {
        let relative = [
            (".cache/huggingface", "AI models"),
            (".ollama", "AI models"),
            (".lmstudio", "AI models"),
            ("Library/Caches", "Caches"),
            (".npm", "Caches"),
            (".cargo/registry", "Caches"),
            (".cache/pip", "Caches"),
            ("Library/CloudStorage", "Cloud downloads"),
            ("Library/Mobile Documents", "Cloud downloads"),
            ("Library/Developer", "Developer tools"),
            ("Library/Android", "Developer tools"),
            (".android", "Developer tools"),
            (".rustup", "Developer tools"),
            (".tart", "Virtual machines"),
            ("Library/Containers/com.docker.docker", "Docker"),
            (".codex/worktrees", "Projects & workspaces"),
            (".codex", "Agent data"),
            ("Desktop/dev", "Projects & workspaces"),
            ("projects", "Projects & workspaces"),
            ("Developer", "Projects & workspaces"),
            ("Downloads", "Downloads"),
            ("Pictures", "Photos & video"),
            ("Movies", "Photos & video"),
            ("Music", "Music"),
            ("Documents", "Documents"),
            ("Desktop", "Desktop"),
            ("Library", "App data"),
        ];
        let mut prefixes: Vec<_> = relative
            .into_iter()
            .map(|(p, c)| (home.join(p), c))
            .collect();
        prefixes.extend([
            (PathBuf::from("/Applications"), "Applications"),
            (PathBuf::from("/Library"), "Shared app data"),
            (PathBuf::from("/private"), "System data"),
            (PathBuf::from("/System"), "System data"),
        ]);
        Self {
            prefixes,
            totals: HashMap::new(),
        }
    }

    pub fn add(&mut self, path: &Path, bytes: u64) {
        let path = alias(path);
        let category = self
            .prefixes
            .iter()
            .find(|(p, _)| path.starts_with(p))
            .map_or("Other files", |(_, category)| *category);
        *self.totals.entry(category).or_default() += bytes;
    }

    pub fn finish(self) -> Vec<StorageCategory> {
        let mut rows: Vec<_> = self
            .totals
            .into_iter()
            .map(|(category, allocated_bytes)| StorageCategory {
                category: category.into(),
                allocated_bytes,
            })
            .collect();
        rows.sort_by(|a, b| {
            b.allocated_bytes
                .cmp(&a.allocated_bytes)
                .then(a.category.cmp(&b.category))
        });
        rows
    }
}
