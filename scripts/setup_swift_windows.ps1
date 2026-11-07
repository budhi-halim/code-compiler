$ErrorActionPreference = "Stop"
$version = "6.4.2"
if ($env:SWIFT_TARGET -eq "windows-arm64") {
  $platform = "windows10-arm64"
} elseif ($env:SWIFT_TARGET -eq "windows-x64") {
  $platform = "windows10"
} else {
  throw "Unsupported Swift Windows build target: $env:SWIFT_TARGET"
}

$filename = "swift-$version-RELEASE-$platform.exe"
$url = "https://download.swift.org/swift-$version-release/$platform/swift-$version-RELEASE/$filename"
$installer = Join-Path $env:RUNNER_TEMP $filename
Write-Host "Downloading official Swift installer for $env:SWIFT_TARGET"
Invoke-WebRequest -Uri $url -OutFile $installer
$install = Start-Process -FilePath $installer -ArgumentList "/quiet", "/norestart" -Wait -PassThru
if ($install.ExitCode -notin @(0, 3010)) {
  throw "Official Swift installation failed: $($install.ExitCode)"
}

$swiftHome = Join-Path $env:LOCALAPPDATA "Programs\Swift"
$compiler = Join-Path $swiftHome "Toolchains\$version+Asserts\usr\bin\swiftc.exe"
$sdk = Join-Path $swiftHome "Platforms\$version\Windows.platform\Developer\SDKs\Windows.sdk"
$runtimeDir = Join-Path $swiftHome "Runtimes\$version\usr\bin"
foreach ($path in @($compiler, $sdk, $runtimeDir)) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Expected Swift installation component was not found: $path"
  }
}

# The selected official installer installs into the user's AppData, not Program Files.
# Swift SDKROOT is essential: without it swiftc cannot load the standard library.
Add-Content -Path $env:GITHUB_ENV -Value "SDKROOT=$sdk"
$compilerDir = Split-Path -Parent $compiler
$paths = @($compilerDir, $runtimeDir)
$paths += @(Get-ChildItem -Path $swiftHome -Filter swiftCore.dll -File -Recurse -ErrorAction SilentlyContinue |
            ForEach-Object { $_.DirectoryName })
foreach ($path in ($paths | Select-Object -Unique)) {
  Add-Content -Path $env:GITHUB_PATH -Value $path
}
Write-Host "Swift SDK: $sdk"
Write-Host "Swift compiler: $compiler"
