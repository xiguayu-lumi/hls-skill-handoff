param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [int]$Width = 1080,

    [int]$Height = 1440,

    [double]$RatioTolerance = 0.01
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputPath -PathType Leaf)) {
    throw "Input image not found: $InputPath"
}

if (Test-Path -LiteralPath $OutputPath) {
    throw "Output already exists; use a versioned filename: $OutputPath"
}

if ($Width -le 0 -or $Height -le 0) {
    throw "Width and Height must be positive."
}

Add-Type -AssemblyName System.Drawing

$source = [System.Drawing.Image]::FromFile($InputPath)
try {
    $sourceRatio = $source.Width / $source.Height
    $targetRatio = $Width / $Height

    if ([Math]::Abs($sourceRatio - $targetRatio) -gt $RatioTolerance) {
        throw "Input ratio $sourceRatio is not close enough to target ratio $targetRatio. Regenerate instead of stretching."
    }

    $outputDir = Split-Path -Parent $OutputPath
    if ($outputDir) {
        New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
    }

    $bitmap = New-Object System.Drawing.Bitmap $Width, $Height
    $bitmap.SetResolution(96, 96)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

    try {
        $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
        $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
        $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $graphics.DrawImage($source, 0, 0, $Width, $Height)
        $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}
finally {
    $source.Dispose()
}

$check = [System.Drawing.Image]::FromFile($OutputPath)
try {
    if ($check.Width -ne $Width -or $check.Height -ne $Height) {
        throw "Output dimension verification failed."
    }

    [pscustomobject]@{
        output_path = $OutputPath
        width = $check.Width
        height = $check.Height
        ratio = [Math]::Round($check.Width / $check.Height, 6)
        bytes = (Get-Item -LiteralPath $OutputPath).Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $OutputPath).Hash
    } | ConvertTo-Json
}
finally {
    $check.Dispose()
}
