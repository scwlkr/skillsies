mod routes;

use std::{collections::BTreeSet, env, path::PathBuf, process::Command};

pub struct Route {
    pub name: &'static str,
    pub program: &'static str,
    pub args: &'static [&'static str],
}

fn help() {
    println!("Project CLI\n\nUsage: ./project <command> [args...]\n");
    println!("  doctor    Check required tools (does not start or test the app)");
    for route in routes::ROUTES {
        println!(
            "  {}    {} {}",
            route.name,
            route.program,
            route.args.join(" ")
        );
    }
    println!("\nExamples:\n  ./project doctor\n  ./project <command> --help");
    println!(
        "\nAdd automation in tools/project-cli/src/routes.rs; route through real app interfaces."
    );
}

fn doctor() -> i32 {
    let mut programs = BTreeSet::from(["cargo", "rustc"]);
    programs.extend(routes::ROUTES.iter().map(|route| route.program));
    let mut missing = false;
    for program in programs {
        match Command::new(program).arg("--version").output() {
            Ok(output) if output.status.success() => println!("{program}=ok"),
            _ => {
                eprintln!("{program}=missing-or-unavailable");
                missing = true;
            }
        }
    }
    println!("app_commands={}", routes::ROUTES.len());
    if routes::ROUTES.is_empty() {
        println!("next=connect app commands in tools/project-cli/src/routes.rs");
    }
    i32::from(missing)
}

fn run() -> i32 {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .to_path_buf();
    if let Err(error) = env::set_current_dir(&root) {
        eprintln!("Cannot enter project {}: {error}", root.display());
        return 1;
    }
    let mut args = env::args().skip(1);
    let name = args.next().unwrap_or_else(|| "--help".into());
    let remaining: Vec<_> = args.collect();
    match name.as_str() {
        "help" | "--help" | "-h" => {
            help();
            0
        }
        "--version" => {
            println!("project-cli {}", env!("CARGO_PKG_VERSION"));
            0
        }
        "doctor" if remaining.iter().any(|arg| arg == "--help" || arg == "-h") => {
            println!("Usage: ./project doctor\nCheck required tools without starting the app.\nExample: ./project doctor");
            0
        }
        "doctor" if remaining.is_empty() => doctor(),
        "doctor" => {
            eprintln!("Usage: ./project doctor");
            2
        }
        _ => {
            let Some(route) = routes::ROUTES.iter().find(|route| route.name == name) else {
                eprintln!("Unknown command: {name}. Run ./project --help.");
                return 2;
            };
            if remaining
                .first()
                .is_some_and(|arg| arg == "--help" || arg == "-h")
            {
                println!("Usage: ./project {} [args...]\nRuns: {} {}\nExample: ./project {}\nPass -- before --help to request the underlying tool's help.",
                    route.name, route.program, route.args.join(" "), route.name);
                return 0;
            }
            let forwarded = if remaining.first().is_some_and(|arg| arg == "--") {
                &remaining[1..]
            } else {
                &remaining[..]
            };
            let mut command = Command::new(route.program);
            command.args(route.args).args(forwarded);
            // Replace ourselves so cancellation and exit status reach the real tool.
            #[cfg(unix)]
            {
                use std::os::unix::process::CommandExt;
                let error = command.exec();
                eprintln!(
                    "Cannot run {}: {error}. Run ./project doctor.",
                    route.program
                );
                127
            }
            #[cfg(not(unix))]
            {
                match command.status() {
                    Ok(status) => status.code().unwrap_or(1),
                    Err(error) => {
                        eprintln!("Cannot run {}: {error}", route.program);
                        127
                    }
                }
            }
        }
    }
}

fn main() {
    std::process::exit(run());
}
