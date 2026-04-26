# setup.ps1 - Creates the personal-ai-agent project structure

Write-Host "Setting up personal-ai-agent..." -ForegroundColor Cyan

$folders = @("crews", "tools", "core", "documents\inbox", "data\qdrant")
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    Write-Host "  Created: $folder" -ForegroundColor Green
}

$files = @(
    "crews\__init__.py",
    "crews\ingestor_crew.py",
    "crews\query_crew.py",
    "tools\__init__.py",
    "tools\pdf_loader.py",
    "tools\doc_classifier.py",
    "tools\qdrant_tool.py",
    "core\__init__.py",
    "core\config.py",
    "core\qdrant_client.py",
    "main.py",
    "requirements.txt",
    ".env",
    ".env.example",
    ".gitignore",
    "README.md",
    "CONTRIBUTING.md",
    "LICENSE"
)

foreach ($file in $files) {
    New-Item -ItemType File -Path $file -Force | Out-Null
    Write-Host "  Created: $file" -ForegroundColor Green
}

Write-Host ""
Write-Host "Structure ready!" -ForegroundColor Cyan