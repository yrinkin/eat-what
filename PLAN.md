# 오늘 뭐 먹지? PLAN

## 작업 원칙
한 번에 아래 작업 하나만 구현한다. 실제로 확인하기 전에는 완료로 표시하지 않는다. 상태는 [ ] 미완료, [x] 확인 완료로 관리하고, 확인 결과는 각 항목 아래에 기록한다. 요구사항 번호는 prd.md의 F01~F13을 따른다.

## 1장: 환경 구성
- [x] T01: MariaDB에 lunch DB와 전용 사용자를 만들고 backend/.env와 .env.example을 준비한다. 확인: 전용 사용자로 접속해 SELECT 1 실행. .env가 git status에 나타나지 않는다.
  - 변경 파일: .gitignore, backend/.env.example, backend/.env(Git 제외, 권한 600), git init
  - 실행: sudo mariadb로 lunch DB(utf8mb4_unicode_ci)와 lunch_app@localhost, lunch_app@127.0.0.1 생성, lunch.* 권한만 부여
  - 확인 결과 (2026-10-14): lunch_app으로 127.0.0.1:3306 TCP 접속과 소켓 접속 모두 SELECT 1 → 1. 권한은 lunch.*에만 있음. git status에 backend/.env가 나타나지 않음.
  - 남은 오류: 없음
- [x] T02: backend/app/main.py, config.py, database.py를 생성하고 GET /api/v1/health를 구현한다. 확인: curl로 200과 status=ok, db=ok. MariaDB를 중지하면 503이 반환된다.
  - 변경 파일: backend/app/__init__.py, config.py, database.py, main.py, backend/requirements.txt, .gitignore(.venv, __pycache__ 추가), backend/.venv(Git 제외)
  - 실행: python3 -m venv .venv, pip install -r requirements.txt, python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  - 확인 결과 (2026-10-14): curl → HTTP 200 {"status":"ok","db":"ok"}. sudo systemctl stop mariadb 후 HTTP 503 {"status":"error","db":"error"}, start 후 다시 200 (사용자 실행). 503 시 로그에 오류 종류만 남고 비밀번호는 없음.
  - 남은 오류: 없음. 8000 포트를 쓰던 flow-task 서버(별도 프로젝트)는 사용자 요청으로 종료함.
- [x] T03: frontend에 Vite + React 프로젝트를 만들고 /api 프록시를 설정한 뒤, 첫 화면에 health 결과를 표시한다. 확인: 브라우저에 db=ok가 표시된다. frontend 코드에서 DB 주소와 계정이 검색되지 않는다.
  - 변경 파일: frontend/ (create-vite 9.2.1 react 템플릿, Vite 8.3, React 19.2), vite.config.js(/api 프록시, 대상은 API_PROXY_TARGET 환경 변수), .env.example, src/App.jsx·App.css·index.css, index.html. 데모 이미지 삭제.
  - 실행: sudo apt install npm(사용자), npm install, npm run dev -- --host 127.0.0.1 --port 5173, npm run lint, npm run build
  - 확인 결과 (2026-10-14): 브라우저에 status ok, db ok 표시(사용자 확인). 5173 프록시 경유 health HTTP 200. node_modules 제외 frontend(dist 포함)에서 3306·lunch_app·DB_*·mysql·mariadb·실제 비밀번호 검색 0건. 빌드 결과에 백엔드 주소 0건. lint·build 오류 없음.
  - 남은 오류: 없음
- [x] T04: API-SPEC.md를 작성한다. 엔드포인트, 요청·응답 예시, 오류 코드(401, 403, 404, 409, 422)를 적는다. 확인: prd.md의 F01~F13이 모두 하나 이상의 API에 대응된다.
  - 변경 파일: API-SPEC.md (엔드포인트 17개, 공통 규칙, 오류 코드표, F01~F13 대응표, PRD에 없어 정한 것 9개)
  - 확인 결과 (2026-10-14): 스크립트로 F01~F13 각각 1개 이상의 API에 대응되고, 대응표의 API가 모두 엔드포인트 목록과 상세 설명에 있음을 확인. 401·403·404·409·422 모두 오류 항목에 기재.
  - 남은 오류: 없음. "PRD에 없어 정한 것" 9개는 사용자 검토 필요.
- [ ] T05: Alembic을 초기화한다. 확인: alembic upgrade head가 오류 없이 실행되고 alembic_version 테이블이 생긴다.

## 2장: 그룹과 멤버
- [ ] T06: groups, members 모델과 마이그레이션을 만든다. 확인: SHOW CREATE TABLE로 invite_code UNIQUE, token UNIQUE, (group_id, nickname) UNIQUE를 확인한다.
- [ ] T07: POST /groups, POST /groups/join, GET /me를 구현한다 (F01, F02). 확인: /docs에서 그룹 생성과 입장 후 토큰으로 /me 조회. 빈 그룹명 422, 중복 닉네임 409, 없는 초대 코드 404, 토큰 없음 401.
- [ ] T08: 입장 화면을 만들고 토큰을 localStorage(lunch-token-v1)에 저장·복원한다. 확인: 일반 창과 시크릿 창에서 다른 닉네임으로 같은 그룹에 입장된다. 새로고침 후에도 유지되고, 토큰을 지우면 입장 화면으로 이동한다.

## 3장: 식당 관리
- [ ] T09: restaurants 모델·마이그레이션과 목록·등록·상세·수정·삭제 API를 구현한다 (F03~F05). 확인: 빈 이름과 잘못된 카테고리 422, 수정 시 미전달 필드 유지, 삭제 204. 삭제한 식당은 목록에서 빠지고 DB에는 deleted_at이 기록된 채 남는다. 다른 그룹의 식당은 404.
- [ ] T10: 샘플 식당 15곳을 등록하는 backend/app/seed.py를 만든다. 확인: 실행 후 해당 그룹의 목록 API가 15곳을 반환한다.
- [ ] T11: 식당 목록 화면과 이름 검색·카테고리 필터를 구현한다 (F06). 확인: 필터 결과 수가 같은 조건의 SQL 조회 결과와 같다. 다른 멤버가 등록한 식당도 보인다.
- [ ] T12: 식당 등록·수정 폼과 삭제 확인을 구현한다. 확인: 삭제를 취소하면 항목이 유지된다. 필터를 건 상태에서 수정해도 다른 항목은 바뀌지 않는다. 이름에 HTML 태그를 넣어도 글자로 표시된다.

## 4장: 카드 뽑기
- [ ] T13: draw_sessions, session_candidates 모델과 services/draw.py 추첨 함수, pytest를 작성한다. 확인: 조건에 맞는 식당이 0곳이면 예외, 2곳이면 2개, 10곳이면 중복 없는 3개. 최대 도보 시간을 지정하면 도보 시간이 null인 식당은 제외된다.
- [ ] T14: POST /draws, GET /draws/current, GET /draws/{id}를 구현한다 (F07, F08). 확인: 0곳 조건 422, 진행 중인 뽑기가 있으면 409. 두 멤버가 조회한 후보가 같다.
- [ ] T15: 뽑기 조건 화면과 DrawCard 뒤집기 컴포넌트를 구현한다. 확인: 카드를 누르면 뒤집히고, 모두 공개된 뒤에만 투표 버튼이 활성화된다. 0곳 조건에서는 안내 문구가 나온다.

## 5장: 투표와 결정
- [ ] T16: votes, visits 모델과 PUT /draws/{id}/vote를 구현한다 (F10). 확인: 같은 멤버가 다시 투표하면 표 수는 그대로이고 선택만 바뀐다. 후보가 아닌 식당은 422, 마감 후 투표는 409.
- [ ] T17: POST /draws/{id}/close를 구현한다 (F11). 확인: 생성자가 아니면 403. 동점과 무투표일 때도 후보 중 하나로 결정된다. 두 번 호출해도 visits는 1건이고, visited_on은 한국 날짜다.
- [ ] T18: usePolling 훅, 득표 표시, 마감 버튼, 결과 화면을 구현한다. 확인: 브라우저 3개에서 투표하면 3초 안에 다른 화면에 반영된다. 마감 결과가 세 화면에서 같다. 탭을 비활성화하면 개발자 도구에서 요청이 멈춘다.

## 6장: 별점과 기록
- [ ] T19: reviews 모델과 GET /visits/pending-review, POST /visits/{id}/reviews를 구현한다 (F12). 확인: 별점 0과 6은 422, 101자 한 줄 평은 422, 같은 방문의 두 번째 별점은 409.
- [ ] T20: 홈 화면의 평가 대기 카드와 별점 입력을 구현한다. 확인: 별점을 등록하면 평가 대기 목록에서 사라진다.
- [ ] T21: 식당 상세 화면을 만들고 목록과 뽑기 카드에 평균 별점을 반영한다 (F13). 확인: 표시된 평균이 SQL AVG 결과를 소수 첫째 자리로 반올림한 값과 같다.

## 7장: 마무리와 시연 배포
- [ ] T22: 다시 뽑기를 구현한다 (F09). 확인: 직전 후보가 제외되고 기존 투표가 초기화된다. 두 번째 요청은 409, 생성자가 아니면 403.
- [ ] T23: 768px 기준 반응형 레이아웃과 로딩·오류 표시를 적용한다. 확인: 개발자 도구에서 360px은 1열·세로 카드, 1280px은 3열 목록·가로 카드. API를 중지하면 오류가 표시된다.
- [ ] T24: 프론트엔드를 빌드하고 Nginx로 정적 파일과 /api 프록시를 구성한다. FastAPI는 systemd(lunch-api)로 등록한다. 확인: 서버 주소로 휴대폰과 PC에서 접속해 뽑기, 투표, 결정, 별점을 끝까지 수행한다. FastAPI를 재시작해도 데이터가 유지된다. 외부에서 3306과 8000 포트에 접속되지 않는다.
- [ ] T25: README.md에 설치와 실행 방법을 정리한다. 확인: 새 폴더에 저장소를 받아 README 순서대로 실행하면 health가 ok를 반환한다.

## 실행 기준
T01: sudo mariadb
T02~T22 백엔드: backend 폴더의 가상환경에서 python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
T03~T23 프론트엔드: frontend 폴더에서 npm run dev -- --host 127.0.0.1 --port 5173
T05 이후 마이그레이션: backend 폴더에서 alembic revision --autogenerate -m "<내용>" 후 alembic upgrade head
T24: npm run build, sudo nginx -t, sudo systemctl reload nginx, sudo systemctl restart lunch-api
실제로 존재하는 파일과 폴더를 확인한 뒤 명령을 실행한다.

## 기록
각 작업마다 변경 파일, 실행 명령, 실제 확인 결과, 남은 오류를 기록한다. 정상 동작을 확인한 작업 단위로 Git 커밋한다.
