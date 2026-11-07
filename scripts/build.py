"""Portable source builder for GitHub Actions. No extra Python packages required.

For custom projects, use the documented conventions in README.md.
Generated files are placed under compiled-output/ in the caller repository.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


def call(*args, cwd=None):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run([str(x) for x in args], cwd=cwd, check=True)


def copy_binary(source, destination):
    if not source.is_file():
        raise FileNotFoundError(f"Compiled executable not found: {source}")
    shutil.copy2(source, destination)
    if os.name != "nt":
        destination.chmod(destination.stat().st_mode | 0o111)


def main():
    workspace = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd())).resolve()
    language = os.environ["COMPILER_LANGUAGE"]
    target = os.environ["COMPILER_TARGET"]
    name = os.environ.get("COMPILER_NAME", "hello").strip()
    requested_project = os.environ.get("COMPILER_PROJECT", "").strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,47}", name):
        raise ValueError("binary_name must be 1-48 characters: letters, numbers, - or _, starting with a letter.")
    if target.startswith("windows-") != (os.name == "nt"):
        raise RuntimeError(f"Runner operating system does not match target {target}")
    project = (workspace / requested_project if requested_project
               else workspace / ".compiler" / "samples" / language).resolve()
    if not project.is_relative_to(workspace):
        raise ValueError("project must be inside the checked-out repository")
    if not project.is_dir():
        raise FileNotFoundError(f"Project directory does not exist: {project}")
    output = workspace / "compiled-output"
    scratch = workspace / ".compiler-build"
    for folder in (output, scratch):
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
    suffix = ".exe" if target.startswith("windows-") else ""
    exe = output / (name + suffix)
    print(f"Compiling {language} / {target} / {project} -> {output}", flush=True)

    if language in ("c", "cpp"):
        build = scratch / "cmake"
        call("cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Release")
        call("cmake", "--build", build, "--config", "Release", "--parallel", "2")
        matches = [p for p in build.rglob(name + suffix) if p.is_file()]
        if not matches:
            raise FileNotFoundError(f"CMake target {name!r} not found under {build}")
        copy_binary(matches[0], exe)

    elif language == "rust":
        call("cargo", "build", "--release", "--manifest-path", project / "Cargo.toml",
             "--target-dir", scratch / "cargo")
        copy_binary(scratch / "cargo" / "release" / (name + suffix), exe)

    elif language == "go":
        call("go", "build", "-trimpath", "-ldflags=-s -w", "-o", exe, ".", cwd=project)

    elif language == "zig":
        call("zig", "build-exe", project / "main.zig", "-O", "ReleaseFast",
             "-femit-bin=" + str(exe))

    elif language == "swift":
        call("swiftc", project / "main.swift", "-O", "-o", exe)

    elif language == "csharp":
        csprojs = list(project.glob("*.csproj"))
        if len(csprojs) != 1:
            raise ValueError(f"Expected exactly one .csproj under {project}")
        rids = {
            "windows-x64": "win-x64", "windows-arm64": "win-arm64",
            "linux-x64": "linux-x64", "linux-arm64": "linux-arm64",
            "macos-x64": "osx-x64", "macos-arm64": "osx-arm64",
        }
        call("dotnet", "publish", csprojs[0], "-c", "Release", "-r", rids[target],
             "--self-contained", "true", "-p:PublishSingleFile=true",
             "-p:DebugType=None", "-p:AssemblyName=" + name,
             "-o", output)
        if not exe.exists():
            raise FileNotFoundError(f".NET apphost missing: {exe}")

    elif language in ("java", "kotlin"):
        staging = scratch / "package"
        staging.mkdir()
        jar = staging / (name + ".jar")
        if language == "java":
            classes = scratch / "classes"
            classes.mkdir()
            call("javac", "-d", classes, project / "Main.java")
            call("jar", "--create", "--file", jar, "--main-class", "Main",
                 "-C", classes, ".")
            main_class = "Main"
        else:
            call("kotlinc.bat" if os.name == "nt" else "kotlinc",
                 project / "Main.kt", "-include-runtime", "-d", jar)
            main_class = "MainKt"
        shutil.copy2(jar, output / jar.name)
        args = ["jpackage", "--type", "app-image", "--name", name,
                "--input", staging, "--main-jar", jar.name,
                "--main-class", main_class, "--dest", output]
        if target.startswith("windows-"):
            args.append("--win-console")
        call(*args)
        bundle = (output / (name + ".app") if target.startswith("macos-")
                  else output / name)
        if not bundle.exists():
            raise FileNotFoundError(f"jpackage app-image missing: {bundle}")
        if target.startswith("windows-"):
            exe = bundle / (name + ".exe")
        elif target.startswith("macos-"):
            exe = bundle / "Contents" / "MacOS" / name
        else:
            exe = bundle / "bin" / name
        if not exe.is_file():
            raise FileNotFoundError(f"Bundled app launcher missing: {exe}")

    else:
        raise ValueError("Unsupported language: " + language)

    # The bundled examples have no args or external resources and can be smoke-tested.
    # A custom program may require configuration/inputs, so only validate its output files.
    if not requested_project:
        print("+ Smoke test:", exe, flush=True)
        p = subprocess.run([str(exe)], check=True, capture_output=True,
                           text=True, timeout=40)
        combined = p.stdout + p.stderr
        print(combined, flush=True)
        if "Hello" not in combined:
            raise RuntimeError("Hello-world smoke test did not produce expected output")

    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {exe.relative_to(output).as_posix()}\n",
                                           encoding="utf-8")
    (output / "build-info.json").write_text(json.dumps({
        "language": language, "target": target, "binary_name": name,
        "project": requested_project or f"samples/{language}",
        "kind": "JVM app image + JAR" if language in ("java", "kotlin")
                else ".NET self-contained single-file" if language == "csharp"
                else "native executable",
        "primary_executable": exe.relative_to(output).as_posix(),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Build and verification successful: {exe}", flush=True)


if __name__ == "__main__":
    main()
