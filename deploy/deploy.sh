#!/usr/bin/env bash
# 오늘 뭐 먹지? 한 대(WSL) 배포 스크립트 (PLAN T24). EC2 3티어는 deploy-db.sh, deploy-back.sh, deploy-front.sh를 쓴다.
# 저장소 루트에서 실행: bash deploy/deploy.sh   (중간에 sudo 비밀번호를 묻는다)
# 하는 일: 화면 빌드 → /var/www/lunch 복사 → Nginx 사이트 교체(task-flow 끄기) → lunch-api 서비스 등록·재시작
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="$(id -un)"
BACKEND_DIR="$ROOT/backend"

echo "[1/5] 화면 빌드"
(cd "$ROOT/frontend" && npm ci --silent && npm run build)

echo "[2/5] 화면 파일을 /var/www/lunch로 복사 (Nginx가 홈 폴더를 읽지 않게 분리)"
sudo mkdir -p /var/www/lunch
sudo rsync -a --delete "$ROOT/frontend/dist/" /var/www/lunch/

echo "[3/5] DB 마이그레이션 확인"
(cd "$BACKEND_DIR" && .venv/bin/alembic upgrade head)

echo "[4/5] lunch-api 서비스 등록 (개발용 uvicorn이 8000번을 쓰고 있으면 먼저 끈다)"
pkill -u "$APP_USER" -f "uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" || true
sed -e "s#__APP_USER__#$APP_USER#g" -e "s#__BACKEND_DIR__#$BACKEND_DIR#g" \
  -e "s#__API_HOST__#127.0.0.1#g" -e "s#__DB_UNIT__#mariadb.service#g" "$ROOT/deploy/lunch-api.service" \
  | sudo tee /etc/systemd/system/lunch-api.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now lunch-api
sudo systemctl restart lunch-api

echo "[5/5] Nginx 사이트 교체 (task-flow는 sites-available에 남겨 두고 연결만 뺀다)"
sed -e "s#__API_UPSTREAM__#127.0.0.1:8000#g" "$ROOT/deploy/nginx-lunch.conf" \
  | sudo tee /etc/nginx/sites-available/lunch > /dev/null
sudo ln -sf /etc/nginx/sites-available/lunch /etc/nginx/sites-enabled/lunch
sudo rm -f /etc/nginx/sites-enabled/task-flow
sudo nginx -t
sudo systemctl reload nginx

sleep 2
echo "확인: $(curl -s http://127.0.0.1/api/v1/health)"
echo "완료. 이 컴퓨터에서는 http://127.0.0.1/ 로 접속한다."
