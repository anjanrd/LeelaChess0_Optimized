$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'C:\Users\HP\Desktop\LC0-B\leela-int8'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
# PREPARED ONLY. Confirm GPU idle manually before invoking this script.
$gpu = & nvidia-smi 2>&1
$gpu | Set-Content -LiteralPath 'reports/logs/studyc_gpu_check.log' -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw 'nvidia-smi failed' }
if (Get-Process -Name lc0 -ErrorAction SilentlyContinue) { throw 'lc0 is already running; leave it untouched and wait' }
$exact = '& ''C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe'' ''-u'' ''ladder.py'' ''studyc'''
$p = Start-Process -FilePath 'C:\Users\HP\Desktop\LC0-B\.venv\Scripts\python.exe' -ArgumentList '"-u" "ladder.py" "studyc"' -WorkingDirectory 'C:\Users\HP\Desktop\LC0-B\leela-int8' -WindowStyle Hidden -RedirectStandardOutput 'reports/logs/studyc_prepared.stdout.log' -RedirectStandardError 'reports/logs/studyc_prepared.stderr.log' -PassThru -Wait
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss K'
Add-Content -LiteralPath LOG.md -Encoding utf8 -Value "[$stamp] Command: $exact; exit=$($p.ExitCode); stdout/stderr: reports/logs/studyc_prepared.*.log"
if ($p.ExitCode -ne 0) { Add-Content -LiteralPath STATUS.md -Encoding utf8 -Value ('| studyc | BLOCKED | exit=' + $p.ExitCode + '; see reports/logs/studyc_prepared.stderr.log |'); exit $p.ExitCode }
