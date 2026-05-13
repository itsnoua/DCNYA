# Aseer Compliance Deployment Script
# This script automates data extraction, building, and pushing to GitHub Pages.

Write-Host "--- 1. Extracting Latest Data ---" -ForegroundColor Cyan
python extract_recurrences.py
python extract_compliance.py

Write-Host "--- 2. Building Frontend ---" -ForegroundColor Cyan
Set-Location frontend
npm run build
Set-Location ..

Write-Host "--- 3. Syncing with Master ---" -ForegroundColor Cyan
git add .
git commit -m "Auto-deploy: Updated data and UI components"
git push origin master

Write-Host "--- 4. Updating GitHub Pages (gh-pages branch) ---" -ForegroundColor Cyan
# This will push the contents of frontend/dist to the gh-pages branch
git subtree push --prefix frontend/dist origin gh-pages

Write-Host "--- DONE! Your site should be live in a few minutes. ---" -ForegroundColor Green
Write-Host "URL: https://itsnoua.github.io/DCNYA/" -ForegroundColor Yellow
