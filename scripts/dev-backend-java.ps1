param(
    [string] $JavaVersion = "21"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
& (Join-Path $PSScriptRoot "use-java.ps1") $JavaVersion
Set-Location (Join-Path $repoRoot "backend-java")
mvn spring-boot:run
