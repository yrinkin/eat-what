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

화면은 `/api`로만 데이터를 요청합니다. DB 접속 정보는 `backend/.env`에만 둡니다. 개발할 때는 Vite 개발 서버가, 배포하면 Nginx가 `/api`를 FastAPI로 넘깁니다. 배포는 서버 한 대([배포 (한 대의 서버)](#배포-한-대의-서버)) 또는 AWS EC2 세 대([배포 (EC2 3티어)](#배포-ec2-3티어))로 할 수 있습니다.

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

## 배포 (EC2 3티어)

화면, API, DB를 EC2 세 대에 나눠 올립니다. 각 서버는 저장소를 `git clone` 해서 필요한 부분만 설치합니다.

| 서버 | 서브넷 | 하는 일 | 확인한 OS |
|---|---|---|---|
| front | 퍼블릭 | Nginx가 화면 파일을 주고 `/api`를 back으로 넘김 | Ubuntu |
| back | 프라이빗 1 | FastAPI(`lunch-api` 서비스, 8000번) | Amazon Linux 2023 |
| db | 프라이빗 2 | MariaDB(3306번) | Amazon Linux 2023 |

준비해 둘 것입니다.

- 프라이빗 서브넷의 기본 경로(`0.0.0.0/0`)가 NAT 게이트웨이를 향해야 `dnf`, `pip`, `git clone`이 됩니다.
- 관리 접속은 SSM으로 합니다. 인스턴스에 `AmazonSSMManagedInstanceCore` 정책이 있는 IAM 역할을 붙입니다.
- 보안 그룹은 IP 대역이 아닌 **보안 그룹 ID**로 허용합니다.

| 보안 그룹 | 인바운드 | 소스 |
|---|---|---|
| front | 80 | `0.0.0.0/0` |
| back | 8000 | front 보안 그룹 |
| db | 3306 | back 보안 그룹 |

아래에서 `<back IP>`, `<db IP>`는 각 서버의 **프라이빗 IP**입니다. 서버에서 `hostname -I`로 확인합니다. 순서는 db → back → front입니다.

### 1. db 서버

```bash
sudo dnf install -y mariadb105-server     # Ubuntu: sudo apt install -y mariadb-server
sudo systemctl enable --now mariadb       # 재부팅해도 켜지게 한다
```

DB와 전용 사용자를 만듭니다. 비밀번호는 back의 `backend/.env`에 넣을 값과 같아야 합니다. 예: `openssl rand -hex 16`

```bash
git clone https://github.com/yrinkin/eat-what.git && cd eat-what
bash deploy/deploy-db.sh <back IP>        # lunch DB와 lunch_app@<back IP>를 만들고 bind-address를 확인한다
```

`deploy-db.sh`가 bind-address를 고치라고 안내하면 MariaDB 설정 파일의 `bind-address`를 `0.0.0.0`으로 바꾸고 `sudo systemctl restart mariadb`를 실행합니다. 사용자를 `lunch_app@'%'`로 만들어도 동작합니다. 이때도 db 보안 그룹이 back에서 오는 3306만 받으므로 실제로는 back에서만 접속됩니다.

### 2. back 서버

코드는 Python 3.12 이상이 필요합니다. Amazon Linux 2023의 기본 `python3`는 3.9라서 3.12를 따로 설치합니다.

```bash
sudo dnf install -y git python3.12        # Ubuntu 24.04: sudo apt install -y git python3-venv
git clone https://github.com/yrinkin/eat-what.git && cd eat-what
cp backend/.env.example backend/.env && chmod 600 backend/.env
vi backend/.env                           # DB_HOST=<db IP>, DB_PASSWORD=<db에서 만든 비밀번호>
timeout 3 bash -c '</dev/tcp/<db IP>/3306' && echo open   # open이 나와야 한다
bash deploy/deploy-back.sh
```

스크립트는 저장소 루트(`eat-what/`)에서 실행합니다. 가상환경과 패키지 설치, DB 마이그레이션을 하고 `lunch-api` 서비스를 `0.0.0.0:8000`으로 등록합니다. 마지막 줄에 `health: {"status":"ok","db":"ok"}`가 나오면 성공입니다.

### 3. front 서버

Vite 8은 Node.js 20.19 이상 또는 22.12 이상이 필요합니다. Ubuntu 기본 저장소의 `nodejs`는 이보다 오래되어 NodeSource에서 설치합니다.

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs nginx rsync
git clone https://github.com/yrinkin/eat-what.git && cd eat-what
bash deploy/deploy-front.sh <back IP>
```

스크립트는 화면을 빌드해 `/var/www/lunch`에 복사하고, `/api`를 `<back IP>:8000`으로 넘기는 Nginx 설정을 켭니다. Ubuntu는 `sites-available/lunch`, Amazon Linux는 `conf.d/lunch.conf`에 넣습니다. 마지막 줄에 `health: {"status":"ok","db":"ok"}`가 나오면 브라우저에서 `http://<front 공인 IP>/`로 접속합니다.

### 확인

```bash
# front에서
curl http://<back IP>:8000/api/v1/health                                    # ok
timeout 3 bash -c '</dev/tcp/<db IP>/3306' && echo open || echo blocked     # blocked여야 한다
# back에서
sudo systemctl restart lunch-api && sleep 2 && curl http://127.0.0.1:8000/api/v1/health
# db에서
systemctl is-enabled mariadb                                                # enabled
```

### 코드를 바꾼 뒤 다시 배포

```bash
# back
cd ~/eat-what && git pull && bash deploy/deploy-back.sh
# front
cd ~/eat-what && git pull && bash deploy/deploy-front.sh <back IP>
```

### 막혔을 때

| 증상 | 원인과 해결 |
|---|---|
| `bash: deploy/...sh: No such file or directory` | 저장소 루트가 아닌 곳(예: `backend/`)에서 실행했거나, 스크립트가 아직 GitHub에 없습니다. `cd ~/eat-what && git pull` |
| `Access denied for user 'lunch_app'@'localhost'` | `backend/.env`의 `DB_HOST`가 `127.0.0.1`입니다. back에 MariaDB가 설치되어 있으면 그쪽으로 접속합니다. `DB_HOST=<db IP>`로 고칩니다. |
| `Access denied for user 'lunch_app'@'<back IP>'` | db까지는 닿았고 비밀번호가 다릅니다. db에서 `ALTER USER`로 비밀번호를 다시 정하고 `.env`의 `DB_PASSWORD`도 같은 값으로 고칩니다. |
| `Can't connect to MySQL server` | db의 MariaDB가 꺼져 있거나, bind-address가 `127.0.0.1`이거나, 보안 그룹이 막혀 있습니다. |
| `git clone`에서 아이디와 비밀번호를 묻는다 | 저장소 주소가 틀렸습니다. 공개 저장소는 인증 없이 받아집니다. |
| 회원가입이 500 | back에서 `journalctl -u lunch-api --no-pager \| tail -80`으로 마지막 `Error` 줄을 확인합니다. 대부분 DB 연결 문제입니다. |

EC2를 중지했다 켜면 프라이빗 IP는 그대로지만 front의 공인 IP는 바뀝니다. 고정하려면 front에 탄력적 IP를 붙입니다. 인스턴스를 중지해도 NAT 게이트웨이 요금은 계속 나갑니다.

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
deploy/
  deploy.sh           한 대(WSL) 배포
  deploy-db.sh        EC2 db: DB와 사용자 만들기
  deploy-back.sh      EC2 back: 패키지·마이그레이션·lunch-api 서비스
  deploy-front.sh     EC2 front: 화면 빌드·Nginx
  nginx-lunch.conf    Nginx 사이트 템플릿 (/api 대상은 설치할 때 채움)
  lunch-api.service   systemd 서비스 템플릿
```

## 참고

- 시각은 UTC로 저장하고 화면에서 한국 시간으로 보여 줍니다. 방문일은 한국 날짜입니다.
- 사용 중인 MariaDB 11.8은 `innodb_snapshot_isolation`이 켜져 있어, 동시에 같은 행을 고치면 오류 1020이 납니다. 투표·마감·다시 뽑기·별점 API는 이를 막도록 한 문장 upsert나 행 잠금과 재시도를 씁니다. `backend/app/routers/draws.py`, `visits.py`의 주석을 참고하세요.
