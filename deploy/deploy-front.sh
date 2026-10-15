#!/usr/bin/env bash
# 오늘 뭐 먹지? EC2 front 서버 배포 스크립트 (PLAN T27, T30)
# front 서버의 저장소 루트에서 실행: bash deploy/deploy-front.sh <back 사설 IP>   (중간에 sudo 비밀번호를 묻는다)
# 하는 일: 화면 빌드 → /var/www/lunch 복사 → /api를 back으로 넘기는 Nginx 사이트를 80번 기본 서버로 켜기 → health 확인
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACK_IP="${1:-}"

if [[ ! "$BACK_IP" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
  echo "사용법: bash deploy/deploy-front.sh <back 사설 IP>   예: bash deploy/deploy-front.sh 10.0.2.15" >&2
  exit 1
fi

# Vite 8은 Node.js 20.19 이상 또는 22.12 이상이 필요하다. 배포판 기본 nodejs가 더 오래된 경우가 있어 먼저 확인한다.
NODE_VER="$(node -v 2>/dev/null || echo none)"
if [[ "$NODE_VER" =~ ^v([0-9]+)\.([0-9]+)\. ]]; then
  MAJOR="${BASH_REMATCH[1]}"; MINOR="${BASH_REMATCH[2]}"
else
  MAJOR=0; MINOR=0
fi
if ! (( MAJOR > 22 || (MAJOR == 22 && MINOR >= 12) || (MAJOR == 20 && MINOR >= 19) )); then
  echo "Node.js 20.19 이상 또는 22.12 이상이 필요합니다. 현재: $NODE_VER" >&2
  exit 1
fi

for c in nginx rsync curl; do
  if ! command -v "$c" > /dev/null && [[ ! -x "/usr/sbin/$c" ]]; then
    echo "$c가 없습니다. Amazon Linux: sudo dnf install -y $c   Ubuntu: sudo apt install -y $c" >&2
    exit 1
  fi
done

echo "[1/3] 화면 빌드"
(cd "$ROOT/frontend" && npm ci --silent && npm run build)

echo "[2/3] 화면 파일을 /var/www/lunch로 복사"
sudo mkdir -p /var/www/lunch
sudo rsync -a --delete "$ROOT/frontend/dist/" /var/www/lunch/

echo "[3/3] Nginx 사이트 설치 (/api → ${BACK_IP}:8000)"
if [[ -d /etc/nginx/sites-available ]]; then
  # Ubuntu: 기본 사이트는 sites-available에 남겨 두고 연결만 뺀다.
  sed -e "s#__API_UPSTREAM__#${BACK_IP}:8000#g" "$ROOT/deploy/nginx-lunch.conf" \
    | sudo tee /etc/nginx/sites-available/lunch > /dev/null
  sudo ln -sf /etc/nginx/sites-available/lunch /etc/nginx/sites-enabled/lunch
  sudo rm -f /etc/nginx/sites-enabled/default
else
  # Amazon Linux: conf.d에 넣는다. nginx.conf의 기본 서버보다 이 설정의 default_server가 우선한다.
  sed -e "s#__API_UPSTREAM__#${BACK_IP}:8000#g" "$ROOT/deploy/nginx-lunch.conf" \
    | sudo tee /etc/nginx/conf.d/lunch.conf > /dev/null
fi
sudo nginx -t
# Amazon Linux는 설치 직후 Nginx가 꺼져 있어 먼저 켠다.
sudo systemctl enable --now nginx
sudo systemctl reload nginx

sleep 1
echo "health: $(curl -s http://127.0.0.1/api/v1/health)"
echo "완료. 브라우저에서 http://<이 서버 공인 IP>/ 로 접속하세요."
