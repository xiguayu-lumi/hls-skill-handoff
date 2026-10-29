param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$CourseSlug
)

$ErrorActionPreference = 'Stop'
$target = [System.IO.Path]::GetFullPath($ProjectRoot)
if (Test-Path -LiteralPath $target) { throw "Target already exists; refusing to overwrite: $target" }

$skillRoot = Split-Path -Parent $PSScriptRoot
$work = Join-Path $target '03_制作工程\handbook-carousel'
$final = Join-Path $target "05_最终交付\小红书\$CourseSlug"
$directories = @(
    $target,
    (Join-Path $target '01_源素材\官网截图'),
    (Join-Path $target '01_源素材\品牌素材'),
    $work,
    (Join-Path $work 'assets'),
    (Join-Path $target '04_审核记录'),
    $final
)
New-Item -ItemType Directory -Path $directories | Out-Null

Copy-Item -LiteralPath (Join-Path $skillRoot 'assets\template\index.html') -Destination (Join-Path $work 'index.html')
Copy-Item -LiteralPath (Join-Path $skillRoot 'assets\brand\hls-logo-header.png') -Destination (Join-Path $work 'assets\hls-logo-header.png')
Copy-Item -LiteralPath (Join-Path $skillRoot 'assets\brand\hls-watermark.png') -Destination (Join-Path $work 'assets\hls-watermark.png')
Copy-Item -LiteralPath (Join-Path $skillRoot 'scripts\render-carousel.mjs') -Destination (Join-Path $work 'render-carousel.mjs')
Copy-Item -LiteralPath (Join-Path $skillRoot 'scripts\verify-carousel.ps1') -Destination (Join-Path $target '04_审核记录\verify-carousel.ps1')

$rules = @"
# Course Analysis Project Rules

- Output: five 1242×1660 Xiaohongshu carousel images named 01.png through 05.png.
- Official course pages are the source of truth; separate official facts, HLS interpretation and study advice.
- Layout primary color: reduced academic blue #283E7C; it is derived from #1F4CCB by reducing HSL saturation and lightness by 30%. School and HLS logos remain in original colors.
- Header left: full HLS logo. Header right: school logo before English school name.
- Center watermark: light-gray italic HLS at 8% opacity on every page.
- Monash University branch: read `monash-xhs-design`, choose a scene-appropriate layout and imagery, and use school plus HLS footer logos by default; do not apply a fixed layout or lower-page fill target. Use `-OmitSchoolLogo` only with `-VisualProfile Monash` when the user explicitly requests school-logo omission.
- First delivery remains 待审核; do not publish automatically.
- Preserve historical versions; never overwrite a completed version folder.
"@
Set-Content -LiteralPath (Join-Path $target 'CODEX.md') -Value $rules -Encoding utf8

$index = @"
# Course Analysis Project

- Status: 待采集
- Version: $CourseSlug
- Official URL: [替换]
- School display name: [替换]
- Course code: [替换]
- Required delivery: five 1242×1660 PNG files named 01.png through 05.png.
- Next: capture official evidence, fill the HTML template, render the five PNG files, then verify them.
"@
Set-Content -LiteralPath (Join-Path $target '项目索引.md') -Value $index -Encoding utf8

Write-Output ([pscustomobject]@{ ProjectRoot = $target; WorkDir = $work; FinalDir = $final } | ConvertTo-Json)
