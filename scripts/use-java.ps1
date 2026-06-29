param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("8", "17", "21")]
    [string] $Version
)

$ErrorActionPreference = "Stop"

$knownJdks = @{
    "8"  = @("F:\Program Files\Java\jdk1.8.0_341")
    "17" = @("F:\Program Files\Java\jdk17")
    "21" = @(
        "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot",
        "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot",
        "C:\Program Files\Eclipse Adoptium\jdk-21.0.8.9-hotspot",
        "F:\Program Files\Java\jdk21",
        "F:\Program Files\Java\jdk-21"
    )
}

$jdkHome = $knownJdks[$Version] | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $jdkHome) {
    $candidateList = ($knownJdks[$Version] -join "`n  - ")
    throw "JDK $Version was not found. Checked:`n  - $candidateList"
}

$oldPathEntries = $env:Path -split ";" | Where-Object {
    $_ -and
    ($_ -notmatch "\\Java\\jdk[^\\]*\\bin$") -and
    ($_ -notmatch "\\Eclipse Adoptium\\jdk-[^\\]+\\bin$") -and
    ($_ -notmatch "\\Common Files\\Oracle\\Java\\javapath$")
}

$env:JAVA_HOME = $jdkHome
$env:Path = "$jdkHome\bin;" + ($oldPathEntries -join ";")

Write-Host "JAVA_HOME=$env:JAVA_HOME"
java -version
javac -version
