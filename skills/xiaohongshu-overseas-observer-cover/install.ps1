param(
  [string]$Destination = ".codex/skills",
  [switch]$Force
)
$SkillDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Name = Split-Path -Leaf $SkillDir
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
$Target = Join-Path $Destination $Name
if ((Test-Path -LiteralPath $Target) -and -not $Force) {
  throw "Target already exists: $Target. Re-run with -Force only when replacement is intended."
}
if (Test-Path -LiteralPath $Target) {
  Remove-Item -Recurse -LiteralPath $Target
}
Copy-Item -Recurse $SkillDir $Target
Write-Host "Installed $Name to $Target"
Write-Host "Restart Codex only if the skill does not appear automatically."
