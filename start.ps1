# RepoLens 启动脚本（PowerShell）
#
# 优先使用"上一级目录"里的 .venv（本仓库的练习环境），
# 找不到就用系统里的 python。

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$venvPython = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "使用虚拟环境: $venvPython" -ForegroundColor Cyan
    & $venvPython run.py --open
} else {
    Write-Host "使用系统 Python: python" -ForegroundColor Cyan
    python run.py --open
}
