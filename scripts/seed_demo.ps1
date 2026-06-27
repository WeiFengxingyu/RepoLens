param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$SkipBenchmark
)

$ErrorActionPreference = "Stop"

function Invoke-RepoLensJson {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Path,
        [object]$Body = $null
    )

    $uri = "$ApiBaseUrl$Path"
    $headers = @{ "Content-Type" = "application/json" }
    if ($null -eq $Body) {
        return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
    }
    $json = $Body | ConvertTo-Json -Depth 20
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body $json
}

function Import-DemoRepository {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Source
    )

    $existing = @(Invoke-RepoLensJson -Method "GET" -Path "/api/repositories")
    $matched = $existing | Where-Object { $_.name -eq $Name -and $_.status -eq "ready" } | Select-Object -First 1
    if ($matched) {
        Write-Host "READY $Name $($matched.id)"
        return $matched
    }

    Write-Host "IMPORT $Name from $Source"
    $imported = Invoke-RepoLensJson -Method "POST" -Path "/api/repositories" -Body @{
        source = $Source
        name = $Name
    }
    if ($imported.status -ne "ready") {
        throw "Repository $Name did not become ready. Status: $($imported.status). Error: $($imported.error_message)"
    }
    Write-Host "READY $Name $($imported.id)"
    return $imported
}

$health = Invoke-RepoLensJson -Method "GET" -Path "/health"
if ($health.status -ne "ok") {
    throw "RepoLens API is not healthy at $ApiBaseUrl."
}

$pythonPath = Join-Path $RepoRoot "evals/demo_repos/python_service"
$tsPath = Join-Path $RepoRoot "evals/demo_repos/ts_webapp"

$pythonRepo = Import-DemoRepository -Name "python_demo" -Source $pythonPath
$tsRepo = Import-DemoRepository -Name "ts_demo" -Source $tsPath

$retrieval = Invoke-RepoLensJson -Method "POST" -Path "/api/repositories/$($pythonRepo.id)/retrieve" -Body @{
    query = "repository import scanner chunk builder"
    top_k = 5
    use_bm25 = $true
    use_vector = $false
    use_graph = $true
}
Write-Host "RETRIEVAL python_demo evidences=$($retrieval.evidences.Count)"

$mcpList = Invoke-RepoLensJson -Method "POST" -Path "/api/mcp" -Body @{
    jsonrpc = "2.0"
    id = "seed-tools"
    method = "tools/list"
    params = @{}
}
Write-Host "MCP tools/list ok=$([bool]$mcpList.result)"

$mcpSearch = Invoke-RepoLensJson -Method "POST" -Path "/api/mcp" -Body @{
    jsonrpc = "2.0"
    id = "seed-search"
    method = "tools/call"
    params = @{
        name = "code.search"
        arguments = @{
            repository_id = $tsRepo.id
            query = "review panel empty diff guard"
            top_k = 5
            use_vector = $false
        }
        client = @{ name = "seed-demo" }
        session_id = "seed-demo-session"
    }
}
Write-Host "MCP code.search isError=$($mcpSearch.result.isError)"

$benchmark = $null
if (-not $SkipBenchmark) {
    $benchmark = Invoke-RepoLensJson -Method "POST" -Path "/api/v1-benchmarks" -Body @{
        name = "Seed Demo V1 Benchmark"
        dataset_path = "evals/datasets/v1_pr_mr_benchmark.jsonl"
        repository_map = @{
            python_demo = $pythonRepo.id
            ts_demo = $tsRepo.id
        }
        include_review = $true
        include_multi_agent = $true
        include_mcp = $true
        top_k = 5
    }
    Write-Host "BENCHMARK status=$($benchmark.status) samples=$($benchmark.sample_count)"
}

$summary = [ordered]@{
    api_base_url = $ApiBaseUrl
    python_demo = @{
        id = $pythonRepo.id
        status = $pythonRepo.status
        files = $pythonRepo.file_count
        chunks = $pythonRepo.chunk_count
    }
    ts_demo = @{
        id = $tsRepo.id
        status = $tsRepo.status
        files = $tsRepo.file_count
        chunks = $tsRepo.chunk_count
    }
    retrieval = @{
        repository_id = $pythonRepo.id
        evidence_count = $retrieval.evidences.Count
        bm25_count = $retrieval.debug.bm25_count
        graph_count = $retrieval.debug.graph_count
    }
    mcp = @{
        tools_listed = $mcpList.result.tools.Count
        code_search_is_error = [bool]$mcpSearch.result.isError
    }
    benchmark = if ($benchmark) {
        @{
            run_id = $benchmark.run_id
            status = $benchmark.status
            sample_count = $benchmark.sample_count
            review = $benchmark.metrics.review
            multi_agent = $benchmark.metrics.multi_agent
            mcp = $benchmark.metrics.mcp
        }
    } else {
        $null
    }
}

$outputPath = Join-Path $RepoRoot ".repolens/demo-seed-summary.json"
$outputDir = Split-Path $outputPath -Parent
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}
$summary | ConvertTo-Json -Depth 20 | Set-Content -Path $outputPath -Encoding utf8

Write-Host "SUMMARY $outputPath"
