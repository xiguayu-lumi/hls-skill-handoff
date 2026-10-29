param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$FinalDir,
    [Parameter(Mandatory = $true)][string]$Html,
    [Parameter(Mandatory = $true)][string]$SchoolDisplayName,
    [string]$CourseCode = '',
    [ValidateSet('Default', 'Birmingham', 'Monash')][string]$VisualProfile = 'Default',
    [switch]$OmitSchoolLogo
)

$ErrorActionPreference = 'Stop'
$errors = [System.Collections.Generic.List[string]]::new()
$isMonash = $VisualProfile -eq 'Monash'
if ($OmitSchoolLogo -and -not $isMonash) {
    $errors.Add('OmitSchoolLogo is supported only with VisualProfile Monash')
}

foreach ($path in @($ProjectRoot, $FinalDir, $Html)) {
    if (-not (Test-Path -LiteralPath $path)) { $errors.Add("Missing path: $path") }
}
if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }

Add-Type -AssemblyName System.Drawing
$pngs = Get-ChildItem -LiteralPath $FinalDir -Filter '*.png' -File | Sort-Object Name
$expected = 1..5 | ForEach-Object { '{0:D2}.png' -f $_ }
if (($pngs.Name -join ',') -ne ($expected -join ',')) { $errors.Add("PNG set mismatch: $($pngs.Name -join ', ')") }

$imageResults = foreach ($png in $pngs) {
    try {
        $image = [System.Drawing.Image]::FromFile($png.FullName)
        $result = [pscustomobject]@{ File = $png.Name; Width = $image.Width; Height = $image.Height; Decode = 'PASS' }
        if ($image.Width -ne 1242 -or $image.Height -ne 1660) { $errors.Add("Wrong dimensions: $($png.Name)") }
        $image.Dispose()
        $result
    } catch {
        $errors.Add("Decode failed: $($png.Name) - $($_.Exception.Message)")
    }
}

$layoutPath = Join-Path $FinalDir 'layout-report.json'
if (-not (Test-Path -LiteralPath $layoutPath)) {
    $errors.Add('Missing layout-report.json')
    $layoutData = @()
} else {
    $layoutData = @(Get-Content -Raw -LiteralPath $layoutPath | ConvertFrom-Json)
    if ($layoutData.Count -ne 5) { $errors.Add("Layout report has $($layoutData.Count) pages") }
    foreach ($page in $layoutData) {
        if ($page.overflow -or $page.width -ne 1242 -or $page.height -ne 1660) { $errors.Add("Layout failure on page $($page.page)") }
    }
}

$htmlText = Get-Content -Raw -LiteralPath $Html
$schoolLogoCount = ([regex]::Matches($htmlText, 'class="(?:school-logo|uq-crest)"')).Count
if ($VisualProfile -eq 'Birmingham') {
    if ($SchoolDisplayName -notmatch '伯明翰大学|University of Birmingham' -or $SchoolDisplayName -match '城市|City') { $errors.Add('Birmingham visual profile requires University of Birmingham') }
    if (([regex]::Matches($htmlText, 'class="hls-footer-logo"')).Count -ne 5) { $errors.Add('Expected 5 HLS footer logos') }
    $visualText = $htmlText
    foreach ($link in [regex]::Matches($htmlText, '(?is)<link\b[^>]*href=["'']([^"'']+\.css)["''][^>]*>')) {
        $cssPath = Join-Path (Split-Path -Parent $Html) $link.Groups[1].Value
        if (Test-Path -LiteralPath $cssPath) { $visualText += Get-Content -Raw -LiteralPath $cssPath }
        else { $errors.Add("Missing local stylesheet: $cssPath") }
    }
    foreach ($colour in @('#fafafa', '#1b1b1b', '#c59a00')) {
        if (-not $visualText.ToLowerInvariant().Contains($colour)) { $errors.Add("Missing Birmingham palette token $colour") }
    }
} elseif ($isMonash) {
    if ($SchoolDisplayName -notmatch '(?i)Monash\s+University|莫纳什大学') { $errors.Add('Monash visual profile requires Monash University/莫纳什大学') }
    if ($SchoolDisplayName -match '(?i)Monash\s+College|莫纳什学院') { $errors.Add('Monash visual profile excludes Monash College/莫纳什学院') }
    if (([regex]::Matches($htmlText, 'class="hls-footer-logo"')).Count -ne 5) { $errors.Add('Expected 5 HLS footer logos for Monash') }
    $visualText = $htmlText
    foreach ($link in [regex]::Matches($htmlText, '(?is)<link\b[^>]*href=["'']([^"'']+\.css)["''][^>]*>')) {
        $cssPath = Join-Path (Split-Path -Parent $Html) $link.Groups[1].Value
        if (Test-Path -LiteralPath $cssPath) { $visualText += Get-Content -Raw -LiteralPath $cssPath }
        else { $errors.Add("Missing local stylesheet: $cssPath") }
    }
    if (-not $visualText.ToLowerInvariant().Contains('#006dae')) { $errors.Add('Missing Monash palette token #006DAE in inline or local CSS') }
} else {
    if (([regex]::Matches($htmlText, 'class="watermark"')).Count -ne 5) { $errors.Add('Expected 5 watermarks') }
    if (([regex]::Matches($htmlText, 'class="hls-header-logo"')).Count -ne 5) { $errors.Add('Expected 5 HLS header logos') }
    if (-not $htmlText.ToLowerInvariant().Contains('#283e7c')) { $errors.Add('Missing reduced layout blue #283E7C') }
    if ($htmlText.ToLowerInvariant().Contains('#1f4ccb')) { $errors.Add('Previous high-brightness HLS blue remains in layout CSS') }
    if ($htmlText.ToLowerInvariant().Contains('#51247a')) { $errors.Add('Legacy UQ purple remains in layout CSS') }
}
if ($isMonash -and $OmitSchoolLogo) {
    if ($schoolLogoCount -ne 0) { $errors.Add('OmitSchoolLogo requires zero school-logo or uq-crest elements') }
} elseif ($schoolLogoCount -ne 5) {
    $errors.Add('Expected 5 school header logos')
}
if (-not $htmlText.Contains($SchoolDisplayName)) { $errors.Add("Missing cover school display name: $SchoolDisplayName") }
if ($CourseCode -and -not $htmlText.Contains($CourseCode)) { $errors.Add("Missing course code: $CourseCode") }
if ($htmlText -match '\{\{[^}]+\}\}|\[替换[^\]]*\]|TODO') { $errors.Add('Unresolved template placeholder found') }
$h1Matches = [regex]::Matches($htmlText, '(?is)<h1\b[^>]*>(.*?)</h1>')
if ($h1Matches.Count -ne 4) {
    $errors.Add("Expected 4 inner-page chapter titles, found $($h1Matches.Count)")
} else {
    for ($index = 0; $index -lt $h1Matches.Count; $index++) {
        $title = [regex]::Replace($h1Matches[$index].Groups[1].Value, '<[^>]+>', '').Trim()
        if ($title -match '[？?]') { $errors.Add("Chapter title must not be a question: $title") }
        if ($title -match '[：:]') { $errors.Add("Chapter title must not contain a colon subtitle: $title") }
    }
}
foreach ($claim in @('保分','包过','代写','代考','老师押题')) {
    if ($htmlText.Contains($claim)) { $errors.Add("Forbidden claim found: $claim") }
}

$report = [pscustomobject]@{
    Timestamp = (Get-Date).ToString('s')
    PngCount = $pngs.Count
    Images = $imageResults
    LayoutPages = $layoutData.Count
    OverflowPages = @($layoutData | Where-Object overflow).Count
    SchoolDisplayName = $SchoolDisplayName
    CourseCode = $CourseCode
    VisualProfile = $VisualProfile
    OmitSchoolLogo = [bool]$OmitSchoolLogo
    Errors = $errors
    Status = if ($errors.Count -eq 0) { 'PASS' } else { 'FAIL' }
}
$report | ConvertTo-Json -Depth 6
if ($errors.Count -gt 0) { exit 1 }
