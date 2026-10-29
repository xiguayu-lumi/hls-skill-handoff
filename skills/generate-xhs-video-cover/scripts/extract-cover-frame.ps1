param(
    [Parameter(Mandatory = $true)]
    [string]$VideoPath,

    [Parameter(Mandatory = $true)]
    [string]$ReviewDir,

    [Parameter(Mandatory = $true)]
    [string]$Prefix,

    [ValidateSet("ContactSheet", "Still")]
    [string]$Mode = "ContactSheet",

    [double]$ChosenTimeSeconds = -1
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $VideoPath -PathType Leaf)) {
    throw "Video not found: $VideoPath"
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw "ffmpeg is not available on PATH."
}

if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
    throw "ffprobe is not available on PATH."
}

New-Item -ItemType Directory -Force -Path $ReviewDir | Out-Null

$durationText = & ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -- $VideoPath
if ($LASTEXITCODE -ne 0) {
    throw "ffprobe failed for: $VideoPath"
}

$duration = [double]::Parse(
    $durationText.Trim(),
    [System.Globalization.CultureInfo]::InvariantCulture
)

if ($duration -le 0) {
    throw "Invalid video duration: $duration"
}

if ($Mode -eq "ContactSheet") {
    $outputPath = Join-Path $ReviewDir "$Prefix-cover-contact-sheet-v1.jpg"
    if (Test-Path -LiteralPath $outputPath) {
        throw "Output already exists; use a new versioned prefix: $outputPath"
    }

    $interval = [Math]::Max(1.0, $duration / 6.0)
    $intervalText = $interval.ToString("0.######", [System.Globalization.CultureInfo]::InvariantCulture)
    $filter = "fps=1/$intervalText,scale=360:-2,tile=3x2"

    & ffmpeg -nostdin -hide_banner -loglevel error -i $VideoPath -vf $filter -frames:v 1 -q:v 2 $outputPath
    if ($LASTEXITCODE -ne 0) {
        throw "ffmpeg contact-sheet extraction failed."
    }

    [pscustomobject]@{
        mode = $Mode
        output_path = $outputPath
        duration_seconds = [Math]::Round($duration, 6)
        interval_seconds = [Math]::Round($interval, 6)
    } | ConvertTo-Json
    exit 0
}

if ($ChosenTimeSeconds -lt 0 -or $ChosenTimeSeconds -ge $duration) {
    throw "ChosenTimeSeconds must be within [0, $duration)."
}

$timeLabel = $ChosenTimeSeconds.ToString("0.###", [System.Globalization.CultureInfo]::InvariantCulture).Replace(".", "p")
$outputPath = Join-Path $ReviewDir "$Prefix-cover-still-${timeLabel}s-v1.png"
if (Test-Path -LiteralPath $outputPath) {
    throw "Output already exists; use a new versioned prefix: $outputPath"
}

$seekText = $ChosenTimeSeconds.ToString("0.######", [System.Globalization.CultureInfo]::InvariantCulture)
& ffmpeg -nostdin -hide_banner -loglevel error -ss $seekText -i $VideoPath -frames:v 1 -compression_level 4 $outputPath
if ($LASTEXITCODE -ne 0) {
    throw "ffmpeg still extraction failed."
}

[pscustomobject]@{
    mode = $Mode
    output_path = $outputPath
    duration_seconds = [Math]::Round($duration, 6)
    chosen_time_seconds = $ChosenTimeSeconds
} | ConvertTo-Json
