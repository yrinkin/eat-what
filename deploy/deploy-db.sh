#!/usr/bin/env bash
# 오늘 뭐 먹지? EC2 db 서버 준비 스크립트 (PLAN T27, T28)
# db 서버의 저장소 루트에서 실행: bash deploy/deploy-db.sh <back 사설 IP>   (sudo 비밀번호와 DB 비밀번호를 묻는다)
# 하는 일: lunch DB 생성 → lunch_app@<back 사설 IP> 생성·권한 부여 → bind-address 확인
# 이미 있는 DB와 사용자는 지우거나 바꾸지 않는다. 비밀번호는 back 서버 backend/.env의 DB_PASSWORD와 같아야 한다.
set -euo pipefail

BACK_IP="${1:-}"
DB_NAME="lunch"
DB_USER="lunch_app"

if [[ ! "$BACK_IP" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
  echo "사용법: bash deploy/deploy-db.sh <back 사설 IP>   예: bash deploy/deploy-db.sh 10.0.2.15" >&2
  exit 1
fi

read -rsp "DB 비밀번호 (back의 DB_PASSWORD와 같은 값): " DB_PASSWORD
echo
# SQL 문자열 안에 넣으므로 따옴표와 역슬래시는 받지 않는다.
if [[ ${#DB_PASSWORD} -lt 12 || "$DB_PASSWORD" == *"'"* || "$DB_PASSWORD" == *"\\"* ]]; then
  echo "비밀번호는 12자 이상이고 ' 와 \\ 가 없어야 합니다. 예: openssl rand -hex 16" >&2
  exit 1
fi

echo "[1/2] DB와 사용자 만들기 (${DB_USER}@${BACK_IP})"
# 비밀번호가 명령줄 인자에 보이지 않도록 표준 입력으로 넘긴다.
sudo mariadb <<SQL
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'${BACK_IP}' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'${BACK_IP}';
FLUSH PRIVILEGES;
SQL
unset DB_PASSWORD
sudo mariadb -e "SELECT user, host FROM mysql.user WHERE user = '${DB_USER}';"

echo "[2/2] bind-address 확인"
BIND="$(sudo mariadb -Nse 'SELECT @@bind_address')"
echo "현재 bind-address: ${BIND:-(비어 있음, 모든 주소)}"
if [[ "$BIND" == "127.0.0.1" || "$BIND" == "localhost" ]]; then
  echo "back에서 접속하려면 MariaDB 설정(Ubuntu: /etc/mysql/mariadb.conf.d/50-server.cnf, Amazon Linux: /etc/my.cnf.d/mariadb-server.cnf)의 bind-address를 0.0.0.0(또는 이 서버의 사설 IP)으로 바꾸고"
  echo "sudo systemctl restart mariadb 를 실행하세요. 3306번은 보안 그룹에서 back 보안 그룹만 허용합니다."
fi
echo "완료. back 서버에서 timeout 3 bash -c '</dev/tcp/<이 서버 사설 IP>/3306' && echo open 으로 확인하세요."
