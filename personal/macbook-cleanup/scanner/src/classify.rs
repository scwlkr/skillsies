use crate::model::{Candidate, Record};
use std::path::{Path, PathBuf};

pub fn alias(path: &Path) -> PathBuf {
    match path.strip_prefix("/System/Volumes/Data") {
        Ok(rest) => Path::new("/").join(rest),
        Err(_) => path.to_owned(),
    }
}

pub fn classify(row: &Record, home: &Path, directory: bool) -> Option<Candidate> {
    let path = alias(&row.path);
    let relative = path.strip_prefix(home).ok();
    let name = path.file_name()?.to_string_lossy();
    // Never call an arbitrary 'target' or 'build' directory disposable.
    let parent = path.parent()?;
    let kind = if directory && name == "target" && parent.join("Cargo.toml").is_file() {
        ("build", "Check the Cargo project and running jobs; rebuildable artifacts can be regenerated with cargo.", "review")
    } else if directory && name == "node_modules" && parent.join("package.json").is_file() {
        ("build", "Check the project, lockfile and running jobs; reinstall dependencies with its package manager.", "review")
    } else if directory && relative == Some(Path::new("Library/Developer/Xcode/DerivedData")) {
        (
            "build",
            "Identify inactive Xcode projects and close builds before clearing their DerivedData.",
            "review",
        )
    } else if directory
        && (relative == Some(Path::new("Library/Caches")) || path == Path::new("/Library/Caches"))
    {
        ("cache", "Inspect the largest app cache children; close the app and prefer its own cache controls. Some caches contain offline downloads.", "review")
    } else if directory
        && matches!(
            relative.and_then(Path::to_str),
            Some(".npm" | ".cache/pip" | ".cargo/registry" | ".cargo/git")
        )
    {
        ("cache", "Confirm packages can be downloaded again and no install/build is running; use the package manager's cache controls.", "review")
    } else if directory
        && matches!(
            relative.and_then(Path::to_str),
            Some(".ollama/models" | ".lmstudio/models" | ".cache/huggingface")
        )
    {
        ("models", "List models and active workloads; remove only selected unused models through their model manager.", "app-managed")
    } else if directory
        && matches!(
            relative.and_then(Path::to_str),
            Some(
                ".tart/vms"
                    | ".android/avd"
                    | "Library/Developer/CoreSimulator"
                    | "Library/Android/sdk"
                    | "Library/Containers/com.docker.docker"
                    | ".rustup/toolchains"
            )
        )
    {
        ("developer assets", "Inventory runtimes, VMs or toolchains with their owning tool; retain active projects/devices. Do not remove the whole directory.", "app-managed")
    } else if directory
        && matches!(
            relative.and_then(Path::to_str),
            Some("Library/CloudStorage" | "Library/Mobile Documents")
        )
    {
        ("cloud", "Verify upload completion and offline needs, then use Finder Remove Download. Deleting a synced file can delete its cloud copy.", "offload")
    } else if directory && relative == Some(Path::new(".Trash")) {
        ("trash", "Review items in Finder Trash, then empty only the approved items; moving to Trash alone does not free disk space.", "review")
    } else if directory
        && name.ends_with(".app")
        && (parent == Path::new("/Applications") || parent == home.join("Applications"))
    {
        ("application", "Confirm the app is unused and use its native uninstaller; preserve stable tools and associated user data.", "app-managed")
    } else if !directory
        && relative.is_some_and(|p| p.starts_with("Downloads"))
        && matches!(
            path.extension().and_then(|s| s.to_str()),
            Some("dmg" | "pkg" | "xip" | "zip")
        )
    {
        ("installer", "Check that installation is complete and this archive is not unique release evidence or a required offline installer.", "review")
    } else {
        return None;
    };
    Some(Candidate {
        path: row.path.clone(),
        allocated_bytes: row.allocated_bytes,
        logical_bytes: row.logical_bytes,
        category: kind.0.into(),
        action: kind.1.into(),
        risk: kind.2.into(),
    })
}

pub fn disjoint(mut rows: Vec<Candidate>) -> Vec<Candidate> {
    rows.sort_by(|a, b| {
        a.path
            .components()
            .count()
            .cmp(&b.path.components().count())
            .then(a.path.cmp(&b.path))
    });
    let mut selected: Vec<Candidate> = Vec::new();
    for row in rows {
        if !selected
            .iter()
            .any(|parent| row.path.starts_with(&parent.path))
        {
            selected.push(row);
        }
    }
    selected.sort_by(|a, b| {
        b.allocated_bytes
            .cmp(&a.allocated_bytes)
            .then(a.path.cmp(&b.path))
    });
    selected
}
