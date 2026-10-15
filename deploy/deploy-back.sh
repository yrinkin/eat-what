#!/usr/bin/env bash
# 오늘 뭐 먹지? EC2 back 서버 배포 스크립트 (PLAN T27, T29)
# back 서버의 저장소 루트에서 실행: bash deploy/deploy-back.sh   (중간에 sudo 비밀번호를 묻는다)
# 준비: backend/.env를 만들어 DB_HOST에 db 서버 사설 IP를 넣는다 (cp backend/.env.example backend/.env, chmod 600).
# 하는 일: 가상환경·패키지 설치 → DB 마이그레이션 → lunch-api 서비스(0.0.0.0:8000) 등록·재시작 → health 확인
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="$(id -un)"
BACKEND_DIR="$ROOT/backend"

if [[ ! -f "$BACKEND_DIR/.env" ]]; then
  echo "backend/.env가 없습니다. cp backend/.env.example backend/.env 후 DB_HOST, DB_PASSWORD를 고치고 chmod 600 하세요." >&2
  exit 1
fi
chmod 600 "$BACKEND_DIR/.env"

# 코드는 Python 3.12 이상이 필요하다. Amazon Linux 2023의 기본 python3는 3.9라서 python3.12를 따로 찾는다.
py_ok() { "$1" -c 'import sys; sys.exit(sys.version_info < (3, 12))' 2>/dev/null; }
PYTHON=""
for p in python3.13 python3.12 python3; do
  if command -v "$p" > /dev/null && py_ok "$p"; then PYTHON="$p"; break; fi
done
if [[ -z "$PYTHON" ]]; then
  echo "Python 3.12 이상이 필요합니다. Amazon Linux: sudo dnf install -y python3.12   Ubuntu: sudo apt install -y python3-venv" >&2
  exit 1
fi
if [[ -d "$BACKEND_DIR/.venv" ]] && ! py_ok "$BACKEND_DIR/.venv/bin/python"; then
  echo "backend/.venv가 Python 3.12 미만으로 만들어져 있습니다. rm -rf backend/.venv 후 다시 실행하세요." >&2
  exit 1
fi

echo "[1/4] 가상환경과 패키지 설치 ($("$PYTHON" -V))"
[[ -d "$BACKEND_DIR/.venv" ]] || "$PYTHON" -m venv "$BACKEND_DIR/.venv"
"$BACKEND_DIR/.venv/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"

echo "[2/4] DB 마이그레이션 (db 서버에 접속되어야 한다)"
(cd "$BACKEND_DIR" && .venv/bin/alembic upgrade head)

echo "[3/4] lunch-api 서비스 등록 (0.0.0.0:8000, 같은 서버에 MariaDB 없음)"
sed -e "s#__APP_USER__#$APP_USER#g" -e "s#__BACKEND_DIR__#$BACKEND_DIR#g" \
  -e "s#__API_HOST__#0.0.0.0#g" -e "s#__DB_UNIT__##g" "$ROOT/deploy/lunch-api.service" \
  | sudo tee /etc/systemd/system/lunch-api.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now lunch-api
sudo systemctl restart lunch-api

echo "[4/4] 확인"
sleep 2
echo "health: $(curl -s http://127.0.0.1:8000/api/v1/health)"
echo "완료. front 서버에서 curl http://<이 서버 사설 IP>:8000/api/v1/health 로 확인하세요."
