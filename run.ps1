# Pack Porter - Windows 启动脚本
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run pack-porter @args
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    $env:PYTHONPATH = if ($env:PYTHONPATH) { "$PSScriptRoot\src;$env:PYTHONPATH" } else { "$PSScriptRoot\src" }
    python -m pack_porter @args
    exit $LASTEXITCODE
}

Write-Host "[错误] 未找到 uv 或 python，请先安装 Python 3.10+ 与 uv（https://docs.astral.sh/uv/）。" -ForegroundColor Red
exit 1
