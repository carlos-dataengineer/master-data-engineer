# Compatibilidade com a v0.2.0. O instalador agora fica na raiz do repositório:
#   irm https://raw.githubusercontent.com/carlos-dataengineer/master-data-engineer/main/install.ps1 | iex
# Este script repassa os parâmetros antigos para ele.
[CmdletBinding()]
param(
    [ValidateSet('User','Project')]
    [string]$Scope = 'User',
    [string]$ProjectPath,
    [switch]$Overwrite
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Installer = Join-Path $Root 'install.ps1'
if (-not (Test-Path $Installer)) { throw "Não encontrei $Installer. Clone o repositório completo." }
$params = @{}
if ($Overwrite) { $params['Force'] = $true }
if ($Scope -eq 'Project') {
    if ([string]::IsNullOrWhiteSpace($ProjectPath)) { throw 'Informe -ProjectPath quando usar -Scope Project.' }
    $params['Project'] = $ProjectPath
}
& $Installer @params
