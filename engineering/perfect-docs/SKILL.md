---
name: PerfectDocs
description: thouroughly investigate the target project and it's current docs so that you can put in place a better and more highly effective doccumentation system,that maximizes agent to human cognition and interaction.
---
# Process to Follow

1. Dive head first into the target projects code base. Get a firm understanding of these things:
  - What is this project, and what is it for?
  - Is this project doing what it currently says it's doing?
  - What stage is this project? 
  - How does this project work, and is it currently in alignment with how the docs say it should work? 
  - What is the target user or issue that is being solved?
  - What architectural systems are in place and fairly rigid, what design decisions are more fluid?
  - How is the project being verified? CI, TDD, Examples, etc.
  - Understand the projects test and running patterns

2. Decide what the docs are currently doing well, and what they are not doing well as compared to the research you did over the whole code base.

3. Implement the **Documentation Structure Template** by adding docs, combing docs, changing docs, deleteing docs etc.


## **Documenation Structure Template**

*template to copy paste is available @/perfect-docs/template

```txt
repo-root/
├─ AGENTS.md
├─ README.md
├─ CHANGELOG.md
│
├─ .codex/
│  └─ config.toml
│
├─ .agents/
│  └─ skills/
│     └─ docs-audit/
│        ├─ SKILL.md
│        ├─ references/
│        │  └─ docs-standard.md
│        └─ scripts/
│
├─ docs/
│  ├─ AGENTS.md
│  ├─ index.md
│  ├─ map.md
│  ├─ status.md
│  │
│  ├─ concepts/
│  │  ├─ project.repo-root/
├─ AGENTS.md
├─ README.md
├─ CHANGELOG.md
│
├─ .codex/
│  └─ config.toml
│
├─ .agents/
│  └─ skills/
│     └─ docs-audit/
│        ├─ SKILL.md
│        ├─ references/
│        │  └─ docs-standard.md
│        └─ scripts/
│
├─ docs/
│  ├─ AGENTS.md
│  ├─ index.md
│  ├─ map.md
│  ├─ status.md
│  │
│  ├─ concepts/
│  │  ├─ index.md
│  │  ├─ project.md
│  │  ├─ workspace.md
│  │  ├─ configuration.md
│  │  └─ core-workflow.md
│  │
│  ├─ guides/
│  │  ├─ index.md
│  │  ├─ installation.md
│  │  ├─ first-run.md
│  │  ├─ create-project.md
│  │  ├─ common-workflows.md
│  │  └─ troubleshooting.md
│  │
│  ├─ reference/
│  │  ├─ index.md
│  │  ├─ cli/
│  │  │  ├─ index.md
│  │  │  ├─ init.md
│  │  │  ├─ run.md
│  │  │  ├─ config.md
│  │  │  └─ help.md
│  │  ├─ config/
│  │  │  ├─ index.md
│  │  │  ├─ fields.md
│  │  │  └─ examples.md
│  │  └─ api/
│  │     ├─ index.md
│  │     ├─ endpoints.md
│  │     └─ schemas.md
│  │
│  ├─ architecture/
│  │  ├─ index.md
│  │  ├─ system-overview.md
│  │  ├─ file-layout.md
│  │  ├─ data-flow.md
│  │  ├─ lifecycle.md
│  │  └─ dependencies.md
│  │
│  ├─ decisions/
│  │  ├─ index.md
│  │  ├─ 0001-docs-structure.md
│  │  └─ 0002-project-architecture.md
│  │
│  └─ todo/
│     ├─ index.md
│     ├─ docs-todo.md
│     ├─ missing-features.md
│     └─ needs-verification.md
│
└─ src/
   └─ ...md
│  │  ├─ workspace.md
│  │  ├─ configuration.md
│  │  └─ core-workflow.md
│  │
│  ├─ guides/
│  │  ├─ index.md
│  │  ├─ installation.md
│  │  ├─ first-run.md
│  │  ├─ create-project.md
│  │  ├─ common-workflows.md
│  │  └─ troubleshooting.md
│  │
│  ├─ reference/
│  │  ├─ index.md
│  │  ├─ cli/
│  │  │  ├─ index.md
│  │  │  ├─ init.md
│  │  │  ├─ run.md
│  │  │  ├─ config.md
│  │  │  └─ help.md
│  │  ├─ config/
│  │  │  ├─ index.md
│  │  │  ├─ fields.md
│  │  │  └─ examples.md
│  │  └─ api/
│  │     ├─ index.md
│  │     ├─ endpoints.md
│  │     └─ schemas.md
│  │
│  ├─ architecture/
│  │  ├─ index.md
│  │  ├─ system-overview.md
│  │  ├─ file-layout.md
│  │  ├─ data-flow.md
│  │  ├─ lifecycle.md
│  │  └─ dependencies.md
│  │
│  │  ├─ index.md
│  │  ├─ 0001-docs-structure.md
│  │  └─ 0002-project-architecture.md
│  │
│  └─ todo/
│     ├─ index.md
│     ├─ docs-todo.md
│     ├─ missing-features.md
│     └─ needs-verification.md
│
└─ src/
   └─ ...
```

## ***Rules that have to be followed for the new documentation structure***

1. Docs must be factual and verified

2. Docs must be current, if they are not current they have to be noted as such *e.g in a todo folder*

3. Docs should be compact so that agents can load them more easily
  - Docs should aim to be 80 - 200 lines
  - Docs cannot be longer than 300 lines unless it is required by the user
  - Docs stay compact by having related/inter links

4. Always keep unverified behavior in a distinct folder away from source of truth docs.

5. the **Documentation Structure Template** is not an exhaustive list and may more be needed but it is a very good structure and should be followed extremely closely unless the user ask otherwise.

6. if there is not enough information to fill out a document it is ok to leave it blank to preserve the structure and wait for the project to mature and have the information to provide later on.

*keep docs small and linked*

## Documentation Structure Explenation

*the general purpose of each doc*

```txt
AGENTS.md                                      # compact repo-level AI/Codex instructions and routing
README.md                                      # human-facing project overview and quick start
CHANGELOG.md                                   # versioned history of notable changes

.codex/                                        # Codex-specific runtime configuration
.codex/config.toml                             # Codex settings like sandboxing, approvals, and repo options

.agents/                                       # reusable AI-agent assets for the project
.agents/skills/                                # modular agent skills/workflows
.agents/skills/docs-audit/                     # reusable workflow for auditing and updating docs
.agents/skills/docs-audit/SKILL.md             # main instructions for the docs-audit skill
.agents/skills/docs-audit/references/          # deeper supporting material for the skill
.agents/skills/docs-audit/references/docs-standard.md # detailed docs rules and standards
.agents/skills/docs-audit/scripts/             # helper scripts used by the skill

docs/                                          # main modular documentation folder
docs/AGENTS.md                                 # docs-folder-specific AI/Codex instructions
docs/index.md                                  # docs homepage and table of contents
docs/map.md                                    # routing file that tells AI what docs to load by task
docs/status.md                                 # truth file for implemented, partial, planned, and unverified behavior

docs/concepts/                                 # explanation docs for project ideas and mental models
docs/concepts/index.md                         # table of contents for concept docs
docs/concepts/project.md                       # explains project purpose, scope, and boundaries
docs/concepts/workspace.md                     # explains what a workspace is and how it is used
docs/concepts/configuration.md                 # explains the configuration model conceptually
docs/concepts/core-workflow.md                 # explains the normal end-to-end workflow

docs/guides/                                   # task-based how-to documentation
docs/guides/index.md                           # table of contents for guides
docs/guides/installation.md                    # how to install the utility
docs/guides/first-run.md                       # fastest path from install to first successful run
docs/guides/create-project.md                  # how to create or initialize a new project/workspace
docs/guides/common-workflows.md                # repeated real-world workflows users perform often
docs/guides/troubleshooting.md                 # common errors, causes, and fixes

docs/reference/                                # exact factual reference documentation
docs/reference/index.md                        # table of contents for reference docs

docs/reference/cli/                            # command-line reference docs
docs/reference/cli/index.md                    # lists all CLI commands and links to command pages
docs/reference/cli/init.md                     # exact reference for the init command
docs/reference/cli/run.md                      # exact reference for the run command
docs/reference/cli/config.md                   # exact reference for the config command
docs/reference/cli/help.md                     # exact reference for the help command

docs/reference/config/                         # configuration reference docs
docs/reference/config/index.md                 # table of contents for config reference
docs/reference/config/fields.md                # every config field, type, default, and behavior
docs/reference/config/examples.md              # copy-pasteable config examples

docs/reference/api/                            # API reference docs if the utility exposes an API
docs/reference/api/index.md                    # table of contents for API reference
docs/reference/api/endpoints.md                # routes, methods, parameters, responses, and errors
docs/reference/api/schemas.md                  # request, response, config, or data schemas

docs/architecture/                             # internal design and system behavior docs
docs/architecture/index.md                     # table of contents for architecture docs
docs/architecture/system-overview.md           # major system parts and how they fit together
docs/architecture/file-layout.md               # repo/source layout and responsibility of major folders
docs/architecture/data-flow.md                 # how data moves from input to output
docs/architecture/lifecycle.md                 # startup, command parsing, execution, shutdown, and errors
docs/architecture/dependencies.md              # important dependencies and why they exist

docs/decisions/                                # architecture decision records
docs/decisions/index.md                        # table of contents for decisions
docs/decisions/0001-docs-structure.md          # why the project uses modular AI-friendly docs
docs/decisions/0002-project-architecture.md    # major architecture decision and tradeoffs

docs/todo/                                     # WIP, planned, missing, uncertain, or unverified docs
docs/todo/index.md                             # table of contents for todo docs
docs/todo/docs-todo.md                         # docs that still need to be written, split, or cleaned
docs/todo/missing-features.md                  # features not implemented yet but planned or discussed
docs/todo/needs-verification.md                # claims or workflows that need source/test verification

src/                                           # main source code folder
src/...                                        # actual implementation files
```