use serde::Serialize;
use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::fs::Metadata;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};

pub fn path_string<S: serde::Serializer>(path: &Path, serializer: S) -> Result<S::Ok, S::Error> {
    serializer.serialize_str(&path.to_string_lossy())
}

pub fn paths_strings<S: serde::Serializer>(
    paths: &[PathBuf],
    serializer: S,
) -> Result<S::Ok, S::Error> {
    use serde::Serialize;
    paths
        .iter()
        .map(|p| p.to_string_lossy())
        .collect::<Vec<_>>()
        .serialize(serializer)
}

#[derive(Clone, Debug)]
pub struct FileMeta {
    pub allocated: u64,
    pub logical: u64,
    pub device: u64,
    pub inode: u64,
    pub links: u64,
    pub modified: i64,
    pub dataless: bool,
}

impl FileMeta {
    pub fn from(meta: &Metadata) -> Self {
        #[cfg(target_os = "macos")]
        let dataless = {
            use std::os::macos::fs::MetadataExt as MacMetadataExt;
            meta.st_flags() & 0x40000000 != 0 // SF_DATALESS in Apple's sys/stat.h.
        };
        #[cfg(not(target_os = "macos"))]
        let dataless = false;
        Self {
            allocated: meta.blocks() * 512,
            logical: meta.size(),
            device: meta.dev(),
            inode: meta.ino(),
            links: meta.nlink(),
            modified: meta.mtime(),
            dataless,
        }
    }
}

#[derive(Clone, Debug, Default, Serialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct Record {
    // Size first makes the bounded heap rank by allocated bytes.
    pub allocated_bytes: u64,
    #[serde(serialize_with = "path_string")]
    pub path: PathBuf,
    pub logical_bytes: u64,
    pub modified_unix: i64,
    pub hard_links: u64,
}

impl Record {
    pub fn new(path: &Path, meta: &FileMeta) -> Self {
        Self {
            path: path.to_owned(),
            allocated_bytes: meta.allocated,
            logical_bytes: meta.logical,
            modified_unix: meta.modified,
            hard_links: meta.links,
        }
    }
    pub fn add(&mut self, other: &Record) {
        self.allocated_bytes += other.allocated_bytes;
        self.logical_bytes += other.logical_bytes;
    }
}

pub fn push_top(heap: &mut BinaryHeap<Reverse<Record>>, record: Record, limit: usize) {
    heap.push(Reverse(record));
    if heap.len() > limit {
        heap.pop();
    }
}

pub fn sorted_top(heap: BinaryHeap<Reverse<Record>>) -> Vec<Record> {
    let mut rows: Vec<_> = heap.into_iter().map(|r| r.0).collect();
    rows.sort_by(|a, b| b.cmp(a));
    rows
}

#[derive(Serialize)]
pub struct Candidate {
    #[serde(serialize_with = "path_string")]
    pub path: PathBuf,
    pub allocated_bytes: u64,
    pub logical_bytes: u64,
    pub category: String,
    pub action: String,
    pub risk: String,
}

#[derive(Default, Serialize)]
pub struct Scan {
    #[serde(serialize_with = "paths_strings")]
    pub roots: Vec<PathBuf>,
    pub elapsed_seconds: f64,
    pub allocated_bytes: u64,
    pub logical_bytes: u64,
    pub files: u64,
    pub directories: u64,
    pub hardlink_duplicates: u64,
    pub external_mounts_skipped: u64,
    pub symlinks_skipped: u64,
    pub dataless_skipped: u64,
    pub error_count: u64,
    pub errors: Vec<String>,
    #[serde(serialize_with = "paths_strings")]
    pub excluded: Vec<PathBuf>,
    pub top_files: Vec<Record>,
    pub top_directories: Vec<Record>,
    pub candidates: Vec<Candidate>,
    pub storage_categories: Vec<crate::storage::StorageCategory>,
}

impl Scan {
    pub fn error(&mut self, error: impl std::fmt::Display) {
        self.error_count += 1;
        if self.errors.len() < 100 {
            self.errors.push(error.to_string());
        }
    }
}
