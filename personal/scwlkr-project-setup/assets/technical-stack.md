Use this as the default for new product work and the migration target for existing products. Implement only the layers and platforms the product needs. Respect explicit user/repository decisions; record deviations and their reasons rather than silently choosing another stack. Existing products: record current → target gaps and a bounded migration in `SETUP-TODO.md`, then track implementation in Linear. Setup changes instructions and tooling, not product code.

| Layer | Tools |
| --- | --- |
| Database | PostgreSQL |
| Backend language | Rust |
| Backend framework | Axum |
| API contract | OpenAPI |
| Validation | Zod |
| Frontend language | TypeScript |
| UI framework | React + React Native |
| App framework | Expo |
| Routing | Expo Router |
| Styling | Tailwind CSS + NativeWind |
| Components | Own shadcn-style UI components |
| Desktop runtime | Electron |
| Desktop packaging | Electron Forge |
| Containers | Docker + Docker Compose |
| Package management | pnpm + Cargo |

| Target | Implementation |
| --- | --- |
| Web | Expo Web / React Native Web |
| iOS + Android | Expo |
| macOS + Windows + Linux | Electron |

- Contracts: OpenAPI describes the Rust/Axum API. Derive TypeScript clients/types and API-boundary Zod schemas from that contract, or verify their alignment; avoid independent, drifting wire definitions. Zod validates TypeScript inputs/responses; Rust validates untrusted server inputs and enforces domain rules. Clients reach PostgreSQL through the backend.
- UI: own component source, tokens, variants and accessibility behavior. Build shared components on React Native primitives with NativeWind; use platform adapters where needed. The shadcn-style ownership/composition pattern does not make DOM-only components native-compatible. Share screens and Expo Router routes across the requested web/mobile targets where practical.
- Desktop: reuse the Expo Web UI in an Electron shell; keep OS integrations in a narrow preload/IPC bridge with context isolation and renderer Node integration disabled. Package with Forge; verify navigation and assets in the packaged app on each claimed OS. For pnpm, follow [Forge's required dependency layout](https://www.electronforge.io/), currently `node-linker=hoisted`.
- Tooling: pnpm owns JavaScript/TypeScript dependencies and Cargo owns Rust dependencies; commit their lockfiles. Preserve an existing declared package manager/lockfile until a migration is implemented. Docker/Compose runs backend and database services; native/desktop builds use their target toolchains. Keep automation behind `./project`.
- Compatibility: resolve supported versions together when implementing; check the selected Expo SDK, React Native, NativeWind/Tailwind and Forge/pnpm combinations against their official docs. Do not impose one Tailwind major across incompatible packages. Verify real behavior on every claimed target; a web build does not qualify mobile or desktop.
