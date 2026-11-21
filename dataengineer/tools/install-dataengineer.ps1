[CmdletBinding()]
param(
    [ValidateSet('User','Project')]
    [string]$Scope = 'User',
    [string]$ProjectPath,
    [switch]$InstallClaude = $true,
    [switch]$InstallCodex = $true,
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
$PackageRoot = Split-Path -Parent $PSScriptRoot
$SkillSource = Join-Path $PackageRoot 'skills\dataengineer'
$ClaudeAgentsSource = Join-Path $PackageRoot 'agents'
$CodexAgentsSource = Join-Path $PackageRoot '.codex\agents'

if (-not (Test-Path (Join-Path $SkillSource 'SKILL.md'))) {
    throw "Não encontrei a skill em $SkillSource"
}

if ($Scope -eq 'Project') {
    if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
        throw 'Informe -ProjectPath quando usar -Scope Project.'
    }
    $Root = [System.IO.Path]::GetFullPath($ProjectPath)
    if (-not (Test-Path $Root)) { throw "A pasta do projeto não existe: $Root" }
    $ClaudeSkills = Join-Path $Root '.claude\skills'
    $ClaudeAgents = Join-Path $Root '.claude\agents'
    $CodexSkills = Join-Path $Root '.agents\skills'
    $CodexAgents = Join-Path $Root '.codex\agents'
} else {
    $Home = $HOME
    $ClaudeSkills = Join-Path $Home '.claude\skills'
    $ClaudeAgents = Join-Path $Home '.claude\agents'
    $CodexSkills = Join-Path $Home '.agents\skills'
    $CodexAgents = Join-Path $Home '.codex\agents'
}

function Copy-PackageDirectory([string]$Source, [string]$Destination) {
    if (Test-Path $Destination) {
        if (-not $Overwrite) {
            Write-Host "PULADO (já existe; use -Overwrite para substituir): $Destination" -ForegroundColor Yellow
            return
        }
        Remove-Item -LiteralPath $Destination -Recurse -Force
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse
    Write-Host "INSTALADO: $Destination" -ForegroundColor Green
}

function Copy-AgentFiles([string]$SourceDirectory, [string]$DestinationDirectory) {
    New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null
    Get-ChildItem -LiteralPath $SourceDirectory -File | ForEach-Object {
        $target = Join-Path $DestinationDirectory $_.Name
        if ((Test-Path $target) -and (-not $Overwrite)) {
            Write-Host "PULADO (agente já existe; use -Overwrite para substituir): $target" -ForegroundColor Yellow
        } else {
            Copy-Item -LiteralPath $_.FullName -Destination $target -Force
            Write-Host "INSTALADO: $target" -ForegroundColor Green
        }
    }
}

if ($InstallClaude) {
    Copy-PackageDirectory $SkillSource (Join-Path $ClaudeSkills 'dataengineer')
    Copy-AgentFiles $ClaudeAgentsSource $ClaudeAgents
}
if ($InstallCodex) {
    Copy-PackageDirectory $SkillSource (Join-Path $CodexSkills 'dataengineer')
    Copy-AgentFiles $CodexAgentsSource $CodexAgents
}

Write-Host ''
Write-Host 'Instalação concluída. Claude Code: /dataengineer | Codex: $dataengineer ou /skills.' -ForegroundColor Cyan
Write-Host 'Reinicie/abra uma sessão nova do agente para recarregar skills e agentes.'
