Defaults → new work; migration target → existing. Needed layers/targets only; user/repo choices prevail; explain deviations. Existing current→target gaps + bounded migration → `SETUP-TODO.md`; implementation → Linear. Setup → instructions/tooling only.

| Layer/target | Tools |
| --- | --- |
| Database | PostgreSQL |
| Backend | Rust + Axum |
| Contract/validation | OpenAPI + Zod |
| UI | TypeScript + React/React Native |
| App/routing | Expo + Expo Router |
| Styling | Tailwind CSS + NativeWind |
| Components | Owned shadcn-style UI |
| Desktop | Electron + Electron Forge |
| Containers | Docker + Compose |
| Packages | pnpm + Cargo |
| Web | Expo Web / React Native Web |
| iOS + Android | Expo |
| macOS + Windows + Linux | Electron |

- Contracts: OpenAPI = Rust/Axum API source; derive TypeScript clients/types + boundary Zod schemas or verify alignment. Zod → TypeScript inputs/responses; Rust → untrusted inputs/domain rules; clients → backend → PostgreSQL.
- UI: own source/tokens/variants/accessibility; React Native primitives + NativeWind; platform adapters as needed. DOM-only shadcn components ≠ native. Share screens/Expo Router routes across requested web/mobile where practical.
- Desktop: Expo Web → Electron shell; OS integration → narrow preload/IPC bridge; context isolation on, renderer Node integration off. Forge packaging → verify navigation/assets on each claimed OS; pnpm → [Forge dependency layout](https://www.electronforge.io/) (`node-linker=hoisted`).
- Tooling: pnpm → JS/TS, Cargo → Rust; commit lockfiles; preserve declared manager/lockfile until migrated. Docker/Compose → backend/database; native/desktop → target toolchains; automation → `./project`.
- Compatibility: check Expo SDK/React Native/NativeWind/Tailwind + Forge/pnpm versions together against official docs; no single Tailwind major across incompatible packages. Prove behavior per claimed target; web build ≠ mobile/desktop proof.
