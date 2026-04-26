# start.ps1 - Activate virtual environment for personal-ai-agent
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
.venv\Scripts\Activate.ps1
Write-Host "personal-ai-agent ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  python main.py ingest              Process documents in inbox/"
Write-Host "  python main.py query '<question>'  Ask a question about your documents"
Write-Host "  python main.py help                Show all commands"