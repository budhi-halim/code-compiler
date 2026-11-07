# code-compiler

Central GitHub Actions build hub for **nine languages** and **six OS/CPU targets**. This repository is public and reusable; you do **not** install compilers on your own computer.

## What is ready

| Language | Windows x64 | Windows ARM64 | Linux x64 | Linux ARM64 | macOS Intel x64 | macOS Apple ARM64 | Output |
|---|---|---|---|---|---|---|---|
| C | yes | yes | yes | yes | yes | yes | native executable |
| C++ | yes | yes | yes | yes | yes | yes | native executable |
| Rust | yes | yes | yes | yes | yes | yes | native executable |
| Go | yes | yes | yes | yes | yes | yes | native executable |
| Zig | yes | yes | yes | yes | yes | yes | native executable |
| C# | yes | yes | yes | yes | yes | yes | self-contained .NET executable (managed code) |
| Java | yes | yes | yes | yes | yes | yes | JAR + jpackage app image with JVM |
| Kotlin | yes | yes | yes | yes | yes | yes | JAR + jpackage app image with JVM |
| Swift | not yet | not yet | yes | yes | yes | yes | native executable |

**Important:** "yes" means a build job has been configured for that platform, **not** that every job has already passed. Look at Actions runs for live results. Windows Swift x64/ARM64 is possible with official Swift toolchains, but it needs separate bootstrap and is intentionally excluded until it can be tested reliably.

## 1. Build a sample here (no local tools)

1. Open the **Actions** tab on this GitHub repository.
2. Select **Multi-platform compiler** in the left sidebar.
3. Click **Run workflow** on the right.
4. Select **Language** = `all` or your chosen language; **Target** = `all` or one of six.
5. Leave **Project** empty and **Binary name** = `hello` for the provided sample projects.
6. Open the finished workflow run. Under **Artifacts**, download `language-target-hello` ZIP.

Choosing `all/all` schedules 52 combinations (Swift on Windows excluded). A push to `master` runs a smaller nine-language smoke matrix on Linux x64 automatically.

## 2. Compile a project kept in another repository

Place this YAML file in your *project repository* as `.github/workflows/build.yml`:

```yaml
name: Compile project
on:
  workflow_dispatch:
jobs:
  compile:
    uses: budhi-halim/code-compiler/.github/workflows/compile.yml@master
    with:
      language: rust
      target: all
      project: .
      binary_name: myapp
    permissions:
      contents: read
```

Use `rust`, `c`, `cpp`, `csharp`, `go`, `zig`, `swift`, `java`, or `kotlin`. `target` accepts `all` or one named target. The workflow checks out **the caller project's code**, then checks out these *public compiler scripts* separately. Build artifacts remain in the **calling project**. A private caller repository stays private. For production, pin the reusable workflow to an audited commit SHA instead of `@master`.

You can also place your projects in a subfolder of this repository and set `project` to that subfolder. Avoid committing private source code here: **this repository is public**.

## 3. Project conventions for the first version

The build script is intentionally minimal, not a general-purpose compiler that guesses arbitrary project layouts.

| Language | Required files in `project` | Output naming rule |
|---|---|---|
| C / C++ | `CMakeLists.txt` | CMake must build target named `binary_name` |
| Rust | `Cargo.toml`, `src/main.rs` | Cargo binary must match `binary_name` |
| Go | `go.mod`, package `main` | compiled as `go build .` |
| Zig | `main.zig` | compiled with `zig build-exe` |
| Swift | `main.swift` | compiled with `swiftc` |
| C# | exactly one `*.csproj` | .NET 10 console executable |
| Java | `Main.java` with class `Main` | JAR and bundled app image |
| Kotlin | `Main.kt` with top-level `main()` | JAR and bundled app image |

For complex projects that use native libraries, special build flags, GUI frameworks, signing, or package managers, adapt `scripts/build.py` or add a specialized build recipe. Platform output is **not** guaranteed portable across OS/CPU types.

## 4. Artifact layout and verification

Each successful job uploads `compiled-output/` with the executable and `build-info.json`, plus `SHA256SUMS.txt` for its primary executable. For Java and Kotlin, an additional portable JAR is included and `jpackage` bundles a private JVM runtime into a platform-specific app image, so these outputs are much larger than C/Go/Rust binaries. C# uses .NET 10 self-contained single-file publishing, not native AOT.

Built-in Hello World projects run a smoke test on the matching runner before upload. Custom projects are built and checked for expected files but are **not automatically executed**, since real programs can require arguments/configuration.

Artifacts expire after 14 days. For long-term distribution, promote verified builds to GitHub Releases using a separate, reviewable release workflow. Signed Windows executables and notarized macOS apps need separate signing credentials/processes.

## Notes

- Public-repository standard Actions runners are generally free, but GitHub's acceptable-use policy and concurrency limits apply.
- Six native runner architectures: `windows-2025`, `windows-11-arm`, `ubuntu-24.04`, `ubuntu-24.04-arm`, `macos-15-intel`, `macos-15`.
- GitHub Actions is the compiler host; only downloaded build outputs occupy your own PC.
- When project dependencies grow, use lockfiles and pin third-party Actions to reviewed commit SHAs.
- The current framework builds single programs, not Windows installers, Python wheels, Android APKs, iOS bundles, or WebAssembly. Those can be added as separate recipes.
- Official runner labels: https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job
