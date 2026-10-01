mod classify;
mod model;
mod storage;
mod walk;

use std::path::PathBuf;

#[derive(Clone)]
pub struct Options {
    roots: Vec<PathBuf>,
    home: PathBuf,
    excludes: Vec<PathBuf>,
    threads: usize,
    top: usize,
    minimum: u64,
}

fn options() -> Result<Options, String> {
    let home = std::env::var_os("HOME")
        .map(PathBuf::from)
        .ok_or("HOME is not set")?;
    let mut options = Options {
        roots: vec![],
        excludes: vec![],
        home,
        threads: 8,
        top: 50,
        minimum: 100 * 1024 * 1024,
    };
    let mut args = std::env::args().skip(1);
    while let Some(flag) = args.next() {
        if flag == "--help" {
            println!("macbook-scan --root PATH [--root PATH] [--home PATH] [--exclude PATH] [--threads 8] [--top 50] [--min-candidate-bytes 104857600]\nRead-only metadata audit; JSON on stdout. Never follows symlinks or crosses filesystems.");
            std::process::exit(0);
        }
        let value = args
            .next()
            .ok_or_else(|| format!("missing value for {flag}"))?;
        match flag.as_str() {
            "--root" => options.roots.push(PathBuf::from(value)),
            "--home" => options.home = PathBuf::from(value),
            "--exclude" => options.excludes.push(PathBuf::from(value)),
            "--threads" => options.threads = value.parse().map_err(|_| "invalid threads")?,
            "--top" => options.top = value.parse().map_err(|_| "invalid top")?,
            "--min-candidate-bytes" => {
                options.minimum = value.parse().map_err(|_| "invalid minimum")?
            }
            _ => return Err(format!("unknown option: {flag}")),
        }
    }
    if options.roots.is_empty() || options.threads == 0 || options.threads > 64 || options.top == 0
    {
        return Err("specify --root; threads must be 1..64 and top must be positive".into());
    }
    Ok(options)
}

fn main() {
    let result = options().and_then(walk::scan).and_then(|scan| {
        serde_json::to_writer(std::io::stdout().lock(), &scan).map_err(|e| e.to_string())
    });
    if let Err(error) = result {
        eprintln!("macbook-scan: {error}");
        std::process::exit(1);
    }
}
