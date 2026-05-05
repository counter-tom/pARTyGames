# deploy.ps1 — run this to build and deploy to AWS
. .\deploy_config.ps1

# 1. Build with pygbag
python -m pygbag --build .

# 2. Restore custom HTML files (pygbag overwrites index.html)
Copy-Item $GAME_PAGE ".\build\web\game.html" -Force
Copy-Item $LOGIN_PAGE ".\build\web\index.html" -Force
Copy-Item $CALLBACK_PAGE ".\build\web\callback.html" -Force

# 3. Upload everything to EC2
scp -i $PEM_PATH -r ".\build\web\." ubuntu@${EC2_IP}:/var/www/html/

Write-Host "Deploy complete! Remember to purge Cloudflare cache."