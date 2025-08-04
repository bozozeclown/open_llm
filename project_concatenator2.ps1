# Alternative PowerShell command that creates a more compact format
$outputFile = "project_compact.txt"
$files = Get-ChildItem -Path . -Recurse -File | 
    Where-Object { 
        $_.Extension -in '.py', '.yaml', '.yml', '.json', '.js', '.css', '.html', '.md', '.txt', '.env' -or 
        $_.Name -eq '.gitignore' -or 
        $_.Name -eq 'webpack.config.js'
    } | 
    Sort-Object FullName

foreach ($file in $files) {
    $relativePath = $file.FullName.Substring((Get-Location).Path.Length + 1)
    "FILE: $relativePath" | Out-File -FilePath $outputFile -Append
    "---START---" | Out-File -FilePath $outputFile -Append
    Get-Content -Path $file.FullName | Out-File -FilePath $outputFile -Append
    "---END---" | Out-File -FilePath $outputFile -Append
    "" | Out-File -FilePath $outputFile -Append
}