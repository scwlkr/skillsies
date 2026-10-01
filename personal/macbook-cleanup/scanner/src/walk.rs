use crate::classify::{alias, classify, disjoint};
use crate::model::{push_top, sorted_top, FileMeta, Record, Scan};
use crate::Options;
use jwalk::{Parallelism, WalkDirGeneric};
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::time::Instant;

fn protected(path: &Path, excludes: &[PathBuf]) -> bool {
    let path = alias(path);
    excludes.iter().any(|p| path.starts_with(alias(p)))
}

fn normalized(path: &Path) -> Result<PathBuf, String> {
    if let Ok(canonical) = fs::canonicalize(path) {
        return Ok(canonical);
    }
    let absolute = if path.is_absolute() {
        path.to_owned()
    } else {
        std::env::current_dir()
            .map_err(|e| e.to_string())?
            .join(path)
    };
    let mut clean = PathBuf::new();
    for part in absolute.components() {
        match part {
            std::path::Component::ParentDir => {
                clean.pop();
            }
            std::path::Component::CurDir => {}
            other => clean.push(other.as_os_str()),
        }
    }
    Ok(clean)
}

pub fn scan(mut options: Options) -> Result<Scan, String> {
    let start = Instant::now();
    options.home = fs::canonicalize(&options.home).map_err(|e| format!("home: {e}"))?;
    options.excludes = options
        .excludes
        .iter()
        .map(|p| normalized(p))
        .collect::<Result<_, _>>()?;
    let mut roots = vec![];
    for root in &options.roots {
        // A symlink supplied as a root is rejected too, before canonicalization.
        let meta = fs::symlink_metadata(root).map_err(|e| format!("{}: {e}", root.display()))?;
        if !meta.is_dir() || meta.file_type().is_symlink() {
            return Err(format!("root must be a real directory: {}", root.display()));
        }
        roots.push(fs::canonicalize(root).map_err(|e| e.to_string())?);
    }
    roots.sort_by_key(|p| p.components().count());
    let mut unique: Vec<PathBuf> = vec![];
    for path in roots {
        if !unique
            .iter()
            .any(|p| path.starts_with(p) || alias(&path).starts_with(alias(p)))
        {
            unique.push(path);
        }
    }
    options.excludes.extend([
        PathBuf::from("/private/var/vm"),
        PathBuf::from("/dev"),
        PathBuf::from("/Volumes"),
        PathBuf::from("/.Spotlight-V100"),
        options.home.join(".tall-talents"),
    ]);
    for root in &unique {
        if protected(root, &options.excludes) {
            return Err(format!("excluded root: {}", root.display()));
        }
    }
    let mut scan = Scan {
        roots: unique.clone(),
        excluded: options.excludes.clone(),
        ..Scan::default()
    };
    let mut directories: HashMap<PathBuf, Record> = HashMap::new();
    let mut hardlinks = HashSet::new();
    let mut top_files = BinaryHeap::new();
    let mut candidates = vec![];
    let mut storage = crate::storage::Storage::new(&options.home);
    for root in &unique {
        let device = fs::symlink_metadata(root).map_err(|e| e.to_string())?.dev();
        let excludes = options.excludes.clone();
        // Store metadata from worker threads so the consumer never stats files twice.
        let walker = WalkDirGeneric::<((), Option<Result<FileMeta, String>>)>::new(root)
            .skip_hidden(false)
            .follow_links(false)
            .sort(false)
            .parallelism(Parallelism::RayonNewPool(options.threads))
            .process_read_dir(move |_, _, _, entries| {
                for entry in entries.iter_mut().filter_map(|e| e.as_mut().ok()) {
                    if entry.file_type.is_symlink() {
                        continue;
                    }
                    let path = entry.path();
                    let metadata = entry
                        .metadata()
                        .map(|m| FileMeta::from(&m))
                        .map_err(|e| format!("{}: {e}", path.display()));
                    if protected(&path, &excludes)
                        || metadata
                            .as_ref()
                            .map_or(true, |m| m.device != device || m.dataless)
                    {
                        entry.read_children = None;
                    }
                    entry.client_state = Some(metadata);
                }
            });
        for entry in walker {
            let entry = match entry {
                Ok(e) => e,
                Err(e) => {
                    scan.error(e);
                    continue;
                }
            };
            let path = entry.path();
            if path.to_str().is_none() {
                scan.error(format!(
                    "Non-UTF8 path displayed lossily; verify with native tools: {}",
                    path.display()
                ));
            }
            if protected(&path, &options.excludes) {
                continue;
            }
            if let Some(error) = entry
                .read_children
                .as_ref()
                .and_then(|children| children.error())
            {
                scan.error(format!("{}: {error}", path.display()));
            }
            if entry.file_type.is_symlink() {
                scan.symlinks_skipped += 1;
                continue;
            }
            let meta = match entry.client_state.unwrap_or_else(|| {
                fs::symlink_metadata(&path)
                    .map(|m| FileMeta::from(&m))
                    .map_err(|e| format!("{}: {e}", path.display()))
            }) {
                Ok(m) => m,
                Err(e) => {
                    scan.error(e);
                    continue;
                }
            };
            if meta.device != device {
                scan.external_mounts_skipped += 1;
                continue;
            }
            if meta.dataless {
                scan.dataless_skipped += 1;
                continue;
            }
            if !entry.file_type.is_dir() && !entry.file_type.is_file() {
                continue;
            }
            let row = Record::new(&path, &meta);
            if entry.file_type.is_dir() {
                scan.directories += 1;
                directories.entry(path.clone()).or_insert(row);
            } else {
                scan.files += 1;
                if meta.links > 1 && !hardlinks.insert((meta.device, meta.inode)) {
                    scan.hardlink_duplicates += 1;
                    continue;
                }
                scan.allocated_bytes += meta.allocated;
                scan.logical_bytes += meta.logical;
                storage.add(&path, meta.allocated);
                if let Some(parent) = path.parent() {
                    directories
                        .entry(parent.to_owned())
                        .or_insert_with(|| Record {
                            path: parent.to_owned(),
                            ..Record::default()
                        })
                        .add(&row);
                }
                if row.allocated_bytes >= options.minimum {
                    if let Some(candidate) = classify(&row, &options.home, false) {
                        candidates.push(candidate);
                    }
                }
                push_top(&mut top_files, row, options.top);
            }
        }
        eprintln!(
            "Scanned {}: {} files, {} coverage errors",
            root.display(),
            scan.files,
            scan.error_count
        );
    }
    // Fold each directory once, from leaves to roots, instead of updating every ancestor per file.
    let mut paths: Vec<_> = directories.keys().cloned().collect();
    paths.sort_by_key(|p| std::cmp::Reverse(p.components().count()));
    let mut top_dirs = BinaryHeap::new();
    for path in paths {
        let row = directories.get(&path).unwrap().clone();
        if row.allocated_bytes >= options.minimum {
            if let Some(candidate) = classify(&row, &options.home, true) {
                candidates.push(candidate);
            }
        }
        if !unique.contains(&path) {
            push_top(&mut top_dirs, row.clone(), options.top);
        }
        if let Some(parent) = path.parent() {
            if let Some(total) = directories.get_mut(parent) {
                total.add(&row);
            }
        }
    }
    // Include directory metadata blocks in the audited allocation total.
    scan.allocated_bytes = unique
        .iter()
        .filter_map(|p| directories.get(p))
        .map(|r| r.allocated_bytes)
        .sum();
    scan.top_files = sorted_top(top_files);
    scan.top_directories = sorted_top(top_dirs);
    scan.candidates = disjoint(candidates);
    scan.storage_categories = storage.finish();
    scan.elapsed_seconds = start.elapsed().as_secs_f64();
    Ok(scan)
}
