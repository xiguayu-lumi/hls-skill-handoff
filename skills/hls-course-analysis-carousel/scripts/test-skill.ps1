param([string]$SkillRoot = (Split-Path -Parent $PSScriptRoot))

$ErrorActionPreference = 'Stop'
$errors = [System.Collections.Generic.List[string]]::new()
$required = @(
    'SKILL.md',
    'CODEX.md',
    'references\research-and-evidence.md',
    'references\content-architecture.md',
    'references\visual-system.md',
    'references\output-and-qa.md',
    'assets\brand\hls-logo-header.png',
    'assets\brand\hls-watermark.png',
    'assets\template\index.html',
    'scripts\scaffold.ps1',
    'scripts\render-carousel.mjs',
    'scripts\verify-carousel.ps1',
    'evals\evals.json'
)
foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $SkillRoot $relative))) { $errors.Add("Missing: $relative") }
}

$skillText = Get-Content -Raw -LiteralPath (Join-Path $SkillRoot 'SKILL.md')
$frontmatter = [regex]::Match($skillText, '(?s)^---\r?\n(.*?)\r?\n---')
if (-not $frontmatter.Success) { $errors.Add('Invalid or missing YAML frontmatter') }
if ($skillText -notmatch '(?m)^name: hls-course-analysis-carousel$') { $errors.Add('Unexpected skill name') }
if ($skillText -notmatch '(?m)^description: .+$') { $errors.Add('Missing description') }
if ($skillText -notmatch '\.\./monash-xhs-design/SKILL\.md') { $errors.Add('Monash visual route is missing') }

$template = Get-Content -Raw -LiteralPath (Join-Path $SkillRoot 'assets\template\index.html')
if (([regex]::Matches($template, 'class="page(?: |")')).Count -ne 5) { $errors.Add('Template does not contain exactly 5 pages') }
if (([regex]::Matches($template, 'class="watermark"')).Count -ne 5) { $errors.Add('Template does not contain 5 watermarks') }
if (([regex]::Matches($template, 'class="hls-header-logo"')).Count -ne 5) { $errors.Add('Template does not contain 5 HLS header logos') }
if (([regex]::Matches($template, 'class="school-logo"')).Count -ne 5) { $errors.Add('Template does not contain 5 school logos') }
if (-not $template.ToLowerInvariant().Contains('#283e7c')) { $errors.Add('Reduced template blue is missing') }
if ($template.ToLowerInvariant().Contains('#1f4ccb')) { $errors.Add('Previous high-brightness blue remains in template') }
if ($template.Contains('#51247a')) { $errors.Add('Legacy UQ purple remains in template') }
if ($template -match 'ECON1050|UQ昆士兰大学|THE UNIVERSITY OF QUEENSLAND') { $errors.Add('UQ-specific facts leaked into reusable template') }
if ($template -notmatch '\{\{COURSE_CODE\}\}') { $errors.Add('Template replacement tokens are missing') }
if ($template -notmatch '课程简介' -or $template -notmatch '考试结构') { $errors.Add('Concise cover navigation labels are missing') }
if ($template -match '<div class="cover-nav">[^\r\n]*(?:学什么|怎么考)') { $errors.Add('Legacy conversational cover navigation remains') }

$scaffoldText = Get-Content -Raw -LiteralPath (Join-Path $SkillRoot 'scripts\scaffold.ps1')
$verifyText = Get-Content -Raw -LiteralPath (Join-Path $SkillRoot 'scripts\verify-carousel.ps1')
if ($verifyText -notmatch "ValidateSet\('Default', 'Birmingham', 'Monash'\)") { $errors.Add('Verifier does not expose Monash visual profile') }
if ($verifyText -notmatch '\[switch\]\$OmitSchoolLogo') { $errors.Add('Verifier does not expose Monash school-logo override') }
if ($scaffoldText -notmatch 'monash-xhs-design') { $errors.Add('Scaffold does not document Monash branch') }
if ($skillText -match '(?i)build-pdf|合并 PDF|五页 PDF') { $errors.Add('Default Skill workflow still requires PDF') }
if ($scaffoldText -match '(?i)build-pdf|PDF') { $errors.Add('Scaffold still creates or requires PDF') }
if ($verifyText -match '(?i)PdfName|pdfinfo|\.pdf') { $errors.Add('Verifier still requires PDF') }

try { Get-Content -Raw -LiteralPath (Join-Path $SkillRoot 'evals\evals.json') | ConvertFrom-Json | Out-Null } catch { $errors.Add("Invalid evals.json: $($_.Exception.Message)") }

$node = 'C:\Users\lgy\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
if (Test-Path -LiteralPath $node) {
    & $node --check (Join-Path $SkillRoot 'scripts\render-carousel.mjs')
    if ($LASTEXITCODE -ne 0) { $errors.Add('render-carousel.mjs syntax check failed') }
}

$result = [pscustomobject]@{ RequiredFiles = $required.Count; Errors = $errors; Status = if ($errors.Count -eq 0) { 'PASS' } else { 'FAIL' } }
$result | ConvertTo-Json -Depth 4
if ($errors.Count -gt 0) { exit 1 }
