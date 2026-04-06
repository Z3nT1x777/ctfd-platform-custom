param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$challengePath = Join-Path $repoRoot $Path

if (-not (Test-Path $challengePath)) {
    throw "Challenge path not found: $challengePath"
}

$requiredFiles = @(
    'challenge.yml'
)

$errors = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path (Join-Path $challengePath $file))) {
        $errors += "Missing required file: $file"
    }
}

$challengeYml = Join-Path $challengePath 'challenge.yml'
$composeYml = Join-Path $challengePath 'docker-compose.yml'

if (Test-Path $challengeYml) {
    $content = Get-Content $challengeYml -Raw
    foreach ($key in @('name', 'category', 'value', 'type', 'description', 'flag')) {
        if ($content -notmatch ("(?m)^{0}:" -f [regex]::Escape($key))) {
            $errors += "challenge.yml missing key: $key"
        }
    }

    $typeMatch = Select-String -Path $challengeYml -Pattern '^type:\s*(\w+)' | Select-Object -First 1
    $challengeType = if ($typeMatch) { $typeMatch.Matches[0].Groups[1].Value } else { '' }

    if ($challengeType -eq 'docker') {
        foreach ($file in @('Dockerfile', 'app.py', 'flag.txt', 'requirements.txt', 'docker-compose.yml')) {
            if (-not (Test-Path (Join-Path $challengePath $file))) {
                $errors += "Missing required file for docker challenge: $file"
            }
        }

        $portMatch = Select-String -Path $challengeYml -Pattern '^port:\s*(\d+)' | Select-Object -First 1
        $containerPortMatch = Select-String -Path $challengeYml -Pattern '^container_port:\s*(\d+)' | Select-Object -First 1
        $containerPort = if ($containerPortMatch) { [int]$containerPortMatch.Matches[0].Groups[1].Value } else { 5000 }
        if (-not $portMatch) {
            $errors += 'challenge.yml missing numeric port for docker challenge'
        } else {
            $port = [int]$portMatch.Matches[0].Groups[1].Value
            if ($port -lt 5001 -or $port -gt 5999) {
                $errors += "Port out of expected range (5001-5999): $port"
            }

            if (Test-Path $composeYml) {
                $compose = Get-Content $composeYml -Raw
                if ($compose -notmatch ("`"{0}:{1}`"" -f $port, $containerPort)) {
                    $errors += "docker-compose.yml does not expose expected port mapping: ${port}:${containerPort}"
                }
            }
        }
    } elseif ($challengeType -eq 'static') {
        if (-not (Test-Path (Join-Path $challengePath 'README.md'))) {
            $errors += 'Missing README.md for static challenge'
        }
    } else {
        $errors += "Unsupported challenge type: $challengeType"
    }
}

if ($errors.Count -gt 0) {
    Write-Host 'Validation FAILED:' -ForegroundColor Red
    $errors | ForEach-Object { Write-Host (" - {0}" -f $_) -ForegroundColor Red }
    exit 1
}

Write-Host 'Validation OK' -ForegroundColor Green
Write-Host ("Challenge path: {0}" -f $Path)
