# 오늘 뭐 먹지?

팀원끼리 같이 쓰는 점심 메뉴 결정 웹앱입니다. 식당 목록에서 카드 뽑기로 후보를 추리고, 투표로 정한 뒤, 다녀와서 별점을 남깁니다.

- 회원가입·로그인 후 그룹을 만들거나 초대 코드로 참여합니다. 한 계정이 여러 그룹에 속할 수 있습니다.
- 조건(제외 카테고리, 가격대, 도보 시간, 가 본 곳/안 가 본 곳)에 맞는 식당 중 최대 3곳을 서버가 무작위로 뽑습니다.
- 멤버가 투표하면 3초 안에 다른 화면에 반영되고, 뽑기를 만든 사람이 마감하면 서버가 결과를 정합니다.
- 다녀온 뒤 별점과 한 줄 평을 남기거나 "안 갔어요"를 고릅니다. 별점이 있는 방문만 실제 방문으로 셉니다.

요구사항은 [PRD.md](PRD.md), 구현 순서와 확인 기록은 [PLAN.md](PLAN.md), API 계약은 [API-SPEC.md](API-SPEC.md)에 있습니다.

## 구성

| 계층 | 기술 | 위치 |
|---|---|---|
| 화면 | React 19 (Vite 8), 배포 시 Nginx | `frontend/` |
| API | FastAPI, SQLAlchemy, Alembic | `backend/` |
| 데이터 | MariaDB | `lunch` DB |

화면은 `/api`로만 데이터를 요청합니다. DB 접속 정보는 `backend/.env`에만 둡니다. 개발할 때는 Vite 개발 서버가, 배포하면 Nginx가 `/api`를 FastAPI로 넘깁니다.

## 준비물

- Python 3.12 이상 (`python3-venv`)
- Node.js 20.19 이상 또는 22.12 이상, npm
- MariaDB 10.6 이상
- 배포할 때만: Nginx, systemd

Ubuntu 기준 설치 예:

```bash
sudo apt install -y python3-venv nodejs npm mariadb-server nginx rsync
```

## 처음 설치

아래 명령은 모두 저장소 루트(`eat-what/`)에서 시작합니다.

### 1. DB와 전용 사용자 만들기

`backend/.env`를 먼저 만들고, 그 비밀번호로 DB 사용자를 만듭니다.

```bash
cp backend/.env.example backend/.env
# backend/.env의 DB_PASSWORD를 실제 비밀번호로 바꾼다. 예: openssl rand -hex 16
chmod 600 backend/.env
```

```bash
set -a && . backend/.env && set +a && sudo mariadb <<SQL
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'127.0.0.1' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL
```

### 2. API 서버

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

다른 터미널에서 확인합니다.

```bash
curl http://127.0.0.1:8000/api/v1/health
# {"status":"ok","db":"ok"}
```

API 문서는 http://127.0.0.1:8000/docs 에서 볼 수 있습니다.

### 3. 화면

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

브라우저에서 http://127.0.0.1:5173 을 열고 회원가입합니다. API 주소를 바꾸려면 `frontend/.env.example`을 `frontend/.env`로 복사해 `API_PROXY_TARGET`을 고칩니다.

### 4. 샘플 식당 넣기 (선택)

화면에서 그룹을 만든 뒤, 그 그룹의 초대 코드로 샘플 식당 15곳을 넣을 수 있습니다.

```bash
cd backend
.venv/bin/python -m app.seed --invite-code 초대코드
```

## 테스트

```bash
cd backend && .venv/bin/python -m pytest      # 추첨·마감 결정 규칙
cd frontend && npm run lint && npm run build  # 화면 문법 검사와 빌드
```

## 배포 (한 대의 서버)

```bash
bash deploy/deploy.sh
```

스크립트가 하는 일입니다. 중간에 sudo 비밀번호를 묻습니다.

1. 화면을 빌드해 `/var/www/lunch`에 복사합니다.
2. DB 마이그레이션을 적용합니다.
3. FastAPI를 systemd 서비스 `lunch-api`로 등록합니다. `127.0.0.1:8000`에서 상시 실행합니다.
4. Nginx 사이트 `lunch`를 80번 기본 서버로 켭니다. 다른 사이트가 80번 기본 서버를 쓰고 있으면 `sites-enabled`에서 연결을 빼야 합니다. 스크립트는 `task-flow` 연결을 뺍니다.

배포 후 확인과 관리 명령입니다.

```bash
curl http://127.0.0.1/api/v1/health
sudo systemctl status lunch-api
sudo systemctl restart lunch-api
journalctl -u lunch-api -f
```

외부에는 Nginx(80번)만 엽니다. MariaDB(3306)와 FastAPI(8000)는 `127.0.0.1`에서만 받습니다.

### WSL에서 휴대폰으로 접속하기

WSL2의 기본 네트워크(NAT)에서는 휴대폰이 WSL에 바로 닿지 않습니다. Windows의 **관리자 PowerShell**에서 80번만 넘겨 줍니다. 휴대폰과 PC가 같은 Wi-Fi에 있어야 합니다.

```powershell
$wsl = (wsl hostname -I).Trim().Split(" ")[0]
netsh interface portproxy add v4tov4 listenport=80 listenaddress=0.0.0.0 connectport=80 connectaddress=$wsl
New-NetFirewallRule -DisplayName "lunch-80" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
ipconfig   # Wi-Fi 어댑터의 IPv4 주소를 휴대폰 브라우저에 입력한다. 예: http://192.168.0.12
```

WSL을 다시 시작하면 WSL 주소가 바뀔 수 있습니다. 그때는 `netsh interface portproxy delete v4tov4 listenport=80 listenaddress=0.0.0.0` 뒤에 위 명령을 다시 실행합니다.

## 폴더 구조

```
backend/
  app/
    main.py           FastAPI 앱과 /api/v1/health
    config.py         backend/.env 읽기
    database.py       DB 연결, 모델 기반 클래스
    deps.py           로그인 세션·그룹 멤버 확인
    models/           SQLAlchemy 모델
    schemas/          요청·응답 형식
    routers/          auth, groups, restaurants, draws, visits
    services/         추첨·마감 결정(draw.py), 별점 통계(stats.py), 비밀번호·토큰(auth.py)
    seed.py           샘플 식당
  alembic/            마이그레이션
  tests/              pytest
frontend/
  src/
    pages/            로그인, 그룹 목록, 그룹 화면
    components/       뽑기, 카드, 식당 목록·상세·폼, 별점 카드
    hooks/usePolling.js  3초 갱신
    api.js, token.js, labels.js
deploy/               Nginx 설정, systemd 서비스, 배포 스크립트
```

## 참고

- 시각은 UTC로 저장하고 화면에서 한국 시간으로 보여 줍니다. 방문일은 한국 날짜입니다.
- 사용 중인 MariaDB 11.8은 `innodb_snapshot_isolation`이 켜져 있어, 동시에 같은 행을 고치면 오류 1020이 납니다. 투표·마감·다시 뽑기·별점 API는 이를 막도록 한 문장 upsert나 행 잠금과 재시도를 씁니다. `backend/app/routers/draws.py`, `visits.py`의 주석을 참고하세요.
