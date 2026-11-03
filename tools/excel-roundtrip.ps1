param(
    [Parameter(Mandatory=$true)][string]$InputCsv,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$sourceCsv = (Resolve-Path -LiteralPath $InputCsv).Path
$destination = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($destination) | Out-Null
foreach ($name in @('text.csv','automatic.csv','evidence.json','input.txt')) {
    if (Test-Path -LiteralPath (Join-Path $destination $name)) { throw "Output already exists: $name" }
}
$importFile = Join-Path $destination 'input.txt'
# Excel's .csv path can select the regional CSV parser; .txt uses OpenText flags.
Copy-Item -LiteralPath $sourceCsv -Destination $importFile
$excelApp = $null
$book = $null
$profiles = @()
try {
    $excelApp = New-Object -ComObject Excel.Application
    $excelApp.Visible = $false
    $excelApp.DisplayAlerts = $false
    $excelApp.AskToUpdateLinks = $false
    $excelApp.AutomationSecurity = 3
    $excelVersion = [string]$excelApp.Version
    $excelBuild = [string]$excelApp.Build
    $missing = [System.Type]::Missing
    foreach ($profile in @('text','automatic')) {
        $fieldInfo = if ($profile -eq 'text') { ,@(@(1,2),@(2,2)) } else { $missing }
        # xlDelimited=1, xlTextQualifierDoubleQuote=1, xlTextFormat=2; explicit comma.
        $excelApp.Workbooks.OpenText($importFile,65001,1,1,1,$false,$false,$false,$true,$false,$false,$missing,$fieldInfo)
        $book = $excelApp.ActiveWorkbook
        if ($book.Worksheets.Item(1).Cells.Item(1,1).Value2 -ne '_rowcanary_id' -or $book.Worksheets.Item(1).Cells.Item(1,2).Value2 -ne '_rowcanary_value') {
            throw 'Import did not produce the two expected control headers'
        }
        if ($profile -eq 'text' -and $book.Worksheets.Item(1).UsedRange.HasFormula -ne $false) {
            throw 'Text import unexpectedly contains a formula'
        }
        $rowCount = $book.Worksheets.Item(1).UsedRange.Rows.Count - 1
        $output = Join-Path $destination ($profile + '.csv')
        # xlCSVUTF8=62; only synthetic cell data is exported, no workbook metadata.
        $book.SaveAs($output,62)
        $book.Close($false)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($book)
        $book = $null
        $profiles += @{name=$profile;rows=$rowCount;output=($profile+'.csv');export_list_separator=[string]$excelApp.International(5)}
    }
    $evidence = @{application='Microsoft Excel';version=$excelVersion;build=$excelBuild;input='RowCanary extended synthetic controls';import='OpenText of byte-identical .txt copy, explicit comma delimiter and UTF-8';encoding='UTF-8';profiles=$profiles;macros='disabled';scope='This installation and these settings only; not a general compatibility certification'}
    $json = $evidence | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText((Join-Path $destination 'evidence.json'),$json,[System.Text.UTF8Encoding]::new($false))
    $json
}
finally {
    if ($null -ne $book) {
        try { $book.Close($false) } catch {}
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($book)
    }
    if ($null -ne $excelApp) {
        try { $excelApp.Quit() } catch {}
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($excelApp)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
