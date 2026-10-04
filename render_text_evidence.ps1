param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [Parameter(Mandatory = $true)]
    [string]$Title
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$lines = [System.IO.File]::ReadAllLines($resolvedInput, [System.Text.Encoding]::UTF8)
$font = [System.Drawing.Font]::new(
    "Consolas",
    16,
    [System.Drawing.FontStyle]::Regular,
    [System.Drawing.GraphicsUnit]::Pixel
)
$titleFont = [System.Drawing.Font]::new(
    "Segoe UI Semibold",
    18,
    [System.Drawing.FontStyle]::Regular,
    [System.Drawing.GraphicsUnit]::Pixel
)
$lineHeight = 22
$padding = 28
$headerHeight = 54

$measureBitmap = [System.Drawing.Bitmap]::new(1, 1)
$measureGraphics = [System.Drawing.Graphics]::FromImage($measureBitmap)
$maxTextWidth = 0
foreach ($line in $lines) {
    $width = [Math]::Ceiling($measureGraphics.MeasureString($line, $font).Width)
    if ($width -gt $maxTextWidth) {
        $maxTextWidth = $width
    }
}
$measureGraphics.Dispose()
$measureBitmap.Dispose()

$width = [Math]::Max(1400, $maxTextWidth + (2 * $padding))
$height = $headerHeight + (2 * $padding) + ($lines.Count * $lineHeight)
$bitmap = [System.Drawing.Bitmap]::new($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.Clear([System.Drawing.Color]::FromArgb(12, 12, 12))
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

$headerBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(35, 35, 38))
$titleBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(235, 235, 235))
$textBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(220, 220, 220))
$graphics.FillRectangle($headerBrush, 0, 0, $width, $headerHeight)
$graphics.DrawString($Title, $titleFont, $titleBrush, $padding, 15)

$y = $headerHeight + $padding
foreach ($line in $lines) {
    $graphics.DrawString($line, $font, $textBrush, $padding, $y)
    $y += $lineHeight
}

$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$bitmap.Save($outputFullPath, [System.Drawing.Imaging.ImageFormat]::Png)

$textBrush.Dispose()
$titleBrush.Dispose()
$headerBrush.Dispose()
$graphics.Dispose()
$bitmap.Dispose()
$titleFont.Dispose()
$font.Dispose()

Write-Output $outputFullPath
