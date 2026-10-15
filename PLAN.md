# 오늘 뭐 먹지? PLAN

## 작업 원칙
한 번에 아래 작업 하나만 구현한다. 실제로 확인하기 전에는 완료로 표시하지 않는다. 상태는 [ ] 미완료, [x] 확인 완료로 관리하고, 확인 결과는 각 항목 아래에 기록한다. 요구사항 번호는 prd.md의 F01~F15를 따른다. T08D 이후 그룹 데이터 API는 /groups/{group_id} 아래 경로를 쓴다(API-SPEC.md 참고).

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
- [x] T05: Alembic을 초기화한다. 확인: alembic upgrade head가 오류 없이 실행되고 alembic_version 테이블이 생긴다.
  - 변경 파일: backend/alembic.ini(접속 URL 줄 제거), backend/alembic/env.py(app.config.settings와 app.database.Base 사용), alembic/script.py.mako, alembic/README, alembic/versions/.gitkeep, backend/app/database.py(Base 추가), backend/requirements.txt(alembic==1.20.0)
  - 실행: pip install alembic, alembic init alembic, alembic upgrade head
  - 확인 결과 (2026-10-14): upgrade head exit 0. 실행 전 테이블 없음 → 실행 후 alembic_version 생성. health 200 유지. alembic 파일에서 비밀번호·계정·포트 검색 0건.
  - 남은 오류: 없음. 리비전은 아직 없음(T06에서 첫 리비전 생성).
  - API-SPEC.md의 "PRD에 없어 정한 것" 9개는 사용자 검토 후 확정함.

## 2장: 그룹과 멤버
- [x] T06: groups, members 모델과 마이그레이션을 만든다. 확인: SHOW CREATE TABLE로 invite_code UNIQUE, token UNIQUE, (group_id, nickname) UNIQUE를 확인한다.
  - 변경 파일: backend/app/models/(__init__.py, base.py, group.py, member.py), backend/app/database.py(제약 이름 규칙), backend/alembic/env.py(app.models 등록), backend/alembic/versions/98332c10d989_create_groups_and_members.py
  - 실행: alembic revision --autogenerate -m "create groups and members", alembic upgrade head
  - 확인 결과 (2026-10-14): SHOW CREATE TABLE에서 uq_groups_invite_code(invite_code), uq_members_token(token), uq_members_group_id_nickname(group_id, nickname), fk_members_group_id_groups 확인. 트랜잭션 시험(ROLLBACK)에서 같은 그룹 같은 닉네임·같은 토큰·없는 그룹은 거절, 다른 그룹 같은 닉네임은 허용. 시험 후 두 테이블 0행. downgrade base → upgrade head 왕복 정상.
  - 남은 오류: 없음. 참고로 utf8mb4_unicode_ci라 닉네임 비교는 대소문자를 구분하지 않음(Minji = minji).
- [x] T07: POST /groups, POST /groups/join, GET /me를 구현한다 (F01, F02). 확인: /docs에서 그룹 생성과 입장 후 토큰으로 /me 조회. 빈 그룹명 422, 중복 닉네임 409, 없는 초대 코드 404, 토큰 없음 401.
  - 변경 파일: backend/app/main.py(라우터 등록), app/errors.py, app/deps.py(get_db, get_current_member), app/services/auth.py(초대 코드·토큰·해시), app/schemas/group.py, app/routers/groups.py
  - 확인 결과 (2026-10-14, curl로 같은 엔드포인트 호출): 그룹 생성 201(공백 제거, 6자리 코드), 소문자·공백 초대 코드로 입장 201, 두 토큰 각각 /me 200. 공백만 있는 그룹명 422, 그룹명 31자 422, 닉네임 21자 422, 앞뒤 공백 붙인 중복 닉네임 409, 없는 초대 코드 404, 토큰 없음 401(WWW-Authenticate: Bearer), 틀린 토큰 401. /docs 200, Bearer 인증 등록 확인. DB에는 토큰 원문 대신 SHA-256(64자)만 저장, created_at은 UTC.
  - 남은 오류: 없음. 시험 데이터(그룹 "T07 테스트팀", 멤버 민지·준호)가 DB에 남아 있음.
- [x] T08: 입장 화면을 만들고 토큰을 localStorage(lunch-token-v1)에 저장·복원한다. 확인: 일반 창과 시크릿 창에서 다른 닉네임으로 같은 그룹에 입장된다. 새로고침 후에도 유지되고, 토큰을 지우면 입장 화면으로 이동한다.
  - 변경 파일: frontend/src/token.js, api.js, pages/EntryPage.jsx, pages/HomePage.jsx, components/ServerStatus.jsx(T03 health 표시 이동), App.jsx, App.css
  - 실행: npm run lint, npm run build, npm run dev -- --host 127.0.0.1 --port 5173
  - 확인 결과 (2026-10-14): lint 경고 0건, build 성공. 5173 프록시로 입장 201, /me 200, 틀린 토큰 401. 브라우저(사용자 확인): 일반 창과 시크릿 창에서 다른 닉네임으로 같은 그룹 입장, 새로고침 후 홈 유지, lunch-token-v1 삭제 후 새로고침하면 입장 화면.
  - 남은 오류: 없음. 같은 탭에서 토큰을 지우면 새로고침해야 반영됨(다른 탭은 storage 이벤트로 바로 반영).

## 2-1장: 계정과 그룹 목록 (2026-10-14 사용자 요청으로 추가)
T07·T08의 "초대 코드 + 닉네임 입장"을 "회원가입·로그인 후 그룹 만들기/참여, 내 그룹 목록"으로 바꾼다. 닉네임은 계정에 하나이며 전체에서 중복 불가. 기존 시험 데이터는 모두 지우고 새로 시작한다(사용자 승인).
- [x] T08A: PRD.md, API-SPEC.md, PLAN.md를 계정 구조에 맞게 수정한다 (F14, F15 추가, F01·F02 수정). 확인: API-SPEC의 F01~F15가 모두 하나 이상의 API에 대응되고, 대응표의 API가 엔드포인트 목록과 상세 설명에 모두 있다.
  - 변경 파일: PRD.md(범위, F14·F15 추가, F01·F02 수정, 데이터, 제외 기능, 완료 기준), API-SPEC.md(인증·오류 코드·계정/그룹 API, 그룹 데이터 경로를 /groups/{group_id} 아래로 이동, 정한 것 10~13 추가), PLAN.md(2-1장 추가)
  - 확인 결과 (2026-10-14): 스크립트로 F01~F15 각각 1개 이상의 API에 대응, 대응표의 API 22개가 엔드포인트 목록과 상세 설명에 모두 있음. 예전 경로(/restaurants 등) 남은 곳 0건.
  - 남은 오류: 없음. 작업 중 API-SPEC 일부가 잘못 잘려 git checkout으로 원본을 되돌린 뒤 다시 적용함.
- [x] T08B: users, sessions 모델을 만들고 members를 (group_id, user_id) 구조로 바꾸는 마이그레이션을 작성한다. 기존 시험 데이터(groups, members, restaurants)는 이 마이그레이션에서 비운다. 확인: SHOW CREATE TABLE로 users.login_id UNIQUE, users.nickname UNIQUE, sessions.token UNIQUE, members (group_id, user_id) UNIQUE를 확인한다. members에 token, nickname 컬럼이 없다.
  - 변경 파일: backend/app/models/user.py(User, UserSession), models/member.py(user_id로 변경, nickname은 계정에서 읽는 속성), models/__init__.py, alembic/versions/28d09940317e_accounts_and_sessions.py(직접 작성)
  - 실행: alembic upgrade head, alembic check, alembic downgrade -1 → upgrade head
  - 확인 결과 (2026-10-14): 적용 전 groups 5·members 8·restaurants 32행 → 적용 후 모두 0행. SHOW CREATE TABLE로 uq_users_login_id, uq_users_nickname, uq_sessions_token, uq_members_group_id_user_id 확인, members에 token·nickname 없음. alembic check "No new upgrade operations detected"(모델과 DB 일치). 트랜잭션 시험(ROLLBACK)에서 중복 아이디·닉네임·세션 토큰·같은 그룹 재참여 모두 거절. downgrade/upgrade 왕복 정상. health 200.
  - 남은 오류: group_id 외래 키가 기존 (group_id, nickname) 인덱스를 쓰고 있어 새 UNIQUE를 먼저 만든 뒤 기존 인덱스를 지우도록 순서를 정함. 기존 /groups, /groups/join, /me, /restaurants API는 예전 members 구조를 써서 T08C·T08D 전까지 동작하지 않음.
- [x] T08C: POST /auth/signup, POST /auth/login, POST /auth/logout, GET /me를 구현한다 (F14, F15). 확인: 회원가입 201 후 토큰으로 /me 200. 중복 아이디·닉네임 409, 형식이 틀린 아이디와 7자 비밀번호 422. 틀린 비밀번호와 없는 아이디는 같은 401 응답. 로그아웃 204 후 같은 토큰으로 /me 401, 다른 기기 토큰은 유지. DB에 비밀번호 원문과 토큰 원문이 없다.
  - 변경 파일: backend/app/services/auth.py(scrypt 비밀번호 해시, 세션 30일), schemas/auth.py, deps.py(get_current_session, get_current_user), routers/auth.py, main.py(auth 라우터 등록, 예전 groups 라우터 해제)
  - 실행: 시험 스크립트(urllib로 API 호출), DB 조회
  - 확인 결과 (2026-10-14): 22/22 통과. 회원가입 201(아이디 소문자·공백 제거) 후 /me 200. 중복 아이디(대문자로 입력해도)·중복 닉네임 409. 아이디 3자·21자·한글·특수문자, 비밀번호 7자·65자, 빈 닉네임 422. 틀린 비밀번호와 없는 아이디는 같은 401 INVALID_CREDENTIALS, 응답 시간 37ms/36ms. 로그아웃 204 후 같은 토큰 /me 401, 다른 로그인 토큰은 200 유지. DB에 비밀번호는 scrypt 해시만, 세션 토큰 원문 0건, 유효 기간 30일. 만료 시각을 과거로 바꾸면 /me 401.
  - 남은 오류: 없음. 처음에 대문자 아이디가 422로 거절됨(StringConstraints의 to_lower가 pattern 검사 뒤에 적용됨) → 검사 전에 소문자로 바꾸도록 수정. 그룹·식당 API는 T08D 전까지 동작하지 않음.
- [x] T08D: GET/POST /groups, POST /groups/join, GET /groups/{group_id}를 구현하고, 식당 API를 /groups/{group_id}/restaurants로 옮긴다. seed.py는 계정 닉네임 기준으로 고친다 (F01, F02). 확인: 그룹 생성 후 다른 계정이 초대 코드로 참여하면 두 계정의 그룹 목록에 모두 나온다. 이미 참여한 그룹 409, 없는 초대 코드 404, 멤버가 아닌 그룹과 그 식당 404. T09의 식당 확인 항목을 새 경로로 다시 통과한다.
  - 변경 파일: backend/app/deps.py(get_current_member: group_id 경로 + 로그인 계정으로 멤버 확인, 아니면 404), schemas/group.py, routers/groups.py(새로 작성), routers/restaurants.py(경로를 /groups/{group_id}/restaurants로), main.py(groups 라우터 다시 등록), seed.py(--nickname은 계정 닉네임)
  - 실행: 시험 스크립트(계정 3개로 urllib 호출), seed.py
  - 확인 결과 (2026-10-14): 50/50 통과. 그룹 생성 후 다른 계정이 소문자 초대 코드로 참여 → 두 계정 목록에 모두 표시, 상세 멤버 목록 참여 순. 이미 참여한 그룹 409 ALREADY_MEMBER, 없는 초대 코드 404, 멤버가 아닌 그룹·없는 그룹 같은 404 GROUP_NOT_FOUND, 로그인 없이 401. 한 계정이 두 그룹에 속하고 최근 참여 순 정렬. T09 식당 항목(422 9종, 미전달 필드 유지, null로 지움, 삭제 204·목록 제외·DB에 deleted_at 남음, 다른 그룹 404)을 새 경로로 모두 통과, created_by는 멤버 id + 계정 닉네임. seed.py --nickname 비 → 15곳 등록, 그룹에 없는 닉네임은 exit 1.
  - 남은 오류: 없음. 시험 데이터(계정 t08d_a·t08d_b·t08d_c, 그룹 "T08D 점심팀"(URND6B)·"T08D 두번째")가 DB에 남아 있음. 화면은 T08E 전까지 예전 방식이라 동작하지 않음.
- [x] T08E: 회원가입·로그인 화면, 로그아웃 버튼, 내 그룹 목록 화면(그룹 만들기, 초대 코드로 참여, 그룹 선택)을 만든다. 확인: 일반 창과 시크릿 창에서 다른 계정으로 같은 그룹에 참여된다. 새로고침 후에도 로그인과 선택한 그룹이 유지된다. 로그아웃하면 로그인 화면으로 이동하고, 다시 로그인하면 그룹 목록이 그대로 있다.
  - 변경 파일: frontend/src/pages/AuthPage.jsx(로그인·회원가입, 비밀번호 확인), pages/GroupListPage.jsx(내 그룹 목록, 참여, 만들기), pages/GroupPage.jsx(초대 코드, 멤버 목록), App.jsx(로그인 → 그룹 목록 → 그룹 화면, 로그아웃, 401이면 로그인 화면), token.js(lunch-group-v1 추가), api.js(401 이벤트), App.css. 삭제: pages/EntryPage.jsx, pages/HomePage.jsx
  - 실행: npm run lint, npm run build, 5173 프록시로 로그인·그룹 목록·로그아웃 호출
  - 확인 결과 (2026-10-14): lint 경고 0건, build 성공. 프록시 경유 로그인 200 → 그룹 목록 → 로그아웃 204 → /me 401. 브라우저(사용자 확인): 일반 창과 시크릿 창에서 다른 계정으로 같은 그룹 참여, 새로고침 후 로그인과 선택한 그룹 유지, 로그아웃하면 로그인 화면, 다시 로그인하면 그룹 목록 그대로.
  - 남은 오류: 없음

## 3장: 식당 관리
- [x] T09: restaurants 모델·마이그레이션과 목록·등록·상세·수정·삭제 API를 구현한다 (F03~F05). 확인: 빈 이름과 잘못된 카테고리 422, 수정 시 미전달 필드 유지, 삭제 204. 삭제한 식당은 목록에서 빠지고 DB에는 deleted_at이 기록된 채 남는다. 다른 그룹의 식당은 404.
  - 변경 파일: backend/app/models/restaurant.py(Category ENUM, 가격대·도보 시간 CHECK), models/__init__.py, schemas/common.py(UTC Z 직렬화, MemberRef), schemas/restaurant.py, routers/restaurants.py, main.py, alembic/versions/349a1875b78f_create_restaurants.py
  - 실행: alembic revision --autogenerate -m "create restaurants", alembic upgrade head, 시험 스크립트(urllib로 API 호출)
  - 확인 결과 (2026-10-14): 30/30 통과. 빈 이름·51자 이름·잘못된/없는 카테고리·가격대 4·도보 61/-1·javascript: 링크·메모 201자 422. 수정 시 미전달 필드 유지, walk_minutes·map_url null로 지움, name null 422. 삭제 204 → 목록에서 빠지고 상세·재삭제 404, DB에 deleted_at 기록된 채 남음. 다른 그룹 GET/PATCH/DELETE 404, 다른 그룹 목록에 안 보임. HTML 태그 이름은 글자 그대로 저장.
  - 남은 오류: 없음. 검색·필터(q, category)는 T11, avg_rating·review_count·last_visited_on·visits는 T16·T19·T21에서 채움(지금은 null/0/[]). 시험 데이터(그룹 "T09 A팀", "T09 B팀")가 DB에 남아 있음.
- [x] T10: 샘플 식당 15곳을 등록하는 backend/app/seed.py를 만든다. 확인: 실행 후 해당 그룹의 목록 API가 15곳을 반환한다.
  - 변경 파일: backend/app/seed.py (초대 코드로 그룹 지정, 등록자는 첫 멤버 또는 --nickname, RestaurantCreate로 검증, 같은 이름은 건너뜀)
  - 실행: backend 폴더에서 .venv/bin/python -m app.seed --invite-code <초대 코드> [--nickname <닉네임>]
  - 확인 결과 (2026-10-14): 새 그룹 "T10 샘플팀"에 실행 → 15곳 등록, 목록 API 15곳(카테고리 7종 모두, 가격대 1·2·3, 도보 null 2곳). 소문자 코드로 다시 실행 → 0곳 등록·15곳 건너뜀, 목록 15곳 유지. 없는 초대 코드·없는 닉네임은 메시지와 함께 exit 1. 다른 그룹 식당 수 변화 없음.
  - 남은 오류: 없음
- [x] T11: 식당 목록 화면과 이름 검색·카테고리 필터를 구현한다 (F06). 확인: 필터 결과 수가 같은 조건의 SQL 조회 결과와 같다. 다른 멤버가 등록한 식당도 보인다.
  - 변경 파일: backend/app/routers/restaurants.py(목록에 q·category, AND, %·_ 이스케이프), frontend/src/components/RestaurantList.jsx(검색 0.3초 대기, 카테고리 선택, 결과 수, 식당 카드), src/labels.js, src/pages/GroupPage.jsx, src/App.css
  - 실행: 시험 스크립트(API 결과 수와 LOCATE 기반 SQL COUNT 비교), npm run lint, npm run build
  - 확인 결과 (2026-10-14): 16/16 통과. 조건 13가지(검색어만·카테고리만·둘 다·앞뒤 공백·%·_·없는 이름)에서 API 결과 수 = SQL 결과 수. '%' 검색은 '100% 국밥_집'만 반환. 잘못된 category 422. 다른 멤버가 등록한 식당도 목록에 보임. 브라우저(사용자 확인): 전체 17·'국' 4·'국'+한식 2·일식 4·'스시'+일식 2곳으로 SQL과 같음, 이름의 <b> 태그는 글자 그대로 표시.
  - 남은 오류: 없음. 평균 별점·최근 방문일은 T19·T21 전까지 '별점 없음'·'방문 기록 없음'으로 표시.
- [x] T12: 식당 등록·수정 폼과 삭제 확인을 구현한다. 확인: 삭제를 취소하면 항목이 유지된다. 필터를 건 상태에서 수정해도 다른 항목은 바뀌지 않는다. 이름에 HTML 태그를 넣어도 글자로 표시된다.
  - 변경 파일: frontend/src/components/RestaurantForm.jsx(등록·수정 폼, 서버와 같은 입력 검사, 수정 시 바뀐 필드만 PATCH), components/RestaurantList.jsx(+ 식당 등록, 카드별 수정·삭제, window.confirm 삭제 확인, 저장·삭제 후 현재 필터로 다시 조회), App.css
  - 실행: npm run lint, npm run build, 브라우저 시험 전후 restaurants 행 비교
  - 확인 결과 (2026-10-14): lint 경고 0건, build 성공. 브라우저(사용자 확인): 삭제 취소 시 항목 유지, 일식 필터 상태에서 수정 저장, 이름에 <i> 태그를 넣어 등록하면 글자 그대로 표시, 빈 이름 저장 시 안내 문구, 삭제 확인 시 목록에서 사라짐. DB 비교(18행 → 19행): 수정한 '돈카츠 연구소'(도보 6→7분)만 변경, 삭제한 '100% 국밥_집'은 deleted_at만 기록되고 행은 남음, 새 식당 1행 추가, 나머지 16행 변경 없음.
  - 남은 오류: 없음

## 4장: 카드 뽑기
- [x] T13: draw_sessions, session_candidates 모델과 services/draw.py 추첨 함수, pytest를 작성한다. 확인: 조건에 맞는 식당이 0곳이면 예외, 2곳이면 2개, 10곳이면 중복 없는 3개. 최대 도보 시간을 지정하면 도보 시간이 null인 식당은 제외된다.
  - 변경 파일: backend/app/models/draw.py(DrawSession, SessionCandidate, open_group_id 계산 컬럼 UNIQUE), models/__init__.py, alembic/versions/86cc431e097a_create_draw_sessions_and_candidates.py, app/services/draw.py(DrawFilters, matches, eligible, pick_candidates, NoCandidatesError), tests/test_draw.py, tests/__init__.py, pytest.ini, requirements.txt(pytest==9.1.1), .gitignore(.pytest_cache)
  - 실행: alembic upgrade head, alembic check, backend 폴더에서 .venv/bin/python -m pytest -v
  - 확인 결과 (2026-10-14): pytest 16 passed. 0곳이면 NoCandidatesError, 2곳이면 2개, 10곳이면 중복 없는 3개(시드 200개), 최대 도보 시간 지정 시 도보 시간 null 제외. 그 밖에 경계값(같은 값 포함), 조건 AND, 삭제 식당 제외, 직전 후보 제외, 모든 후보가 뽑힐 수 있음 확인. 버그를 일부러 넣으면(null 도보 미제외, 중복 허용 추첨) 각각 테스트 2개씩 실패하는 것 확인 후 원복. alembic check 일치. 트랜잭션 시험(ROLLBACK)에서 같은 그룹 두 번째 OPEN 뽑기 거절, 마감 후 새 OPEN 허용.
  - 남은 오류: 없음
- [x] T14: POST /draws, GET /draws/current, GET /draws/{id}를 구현한다 (F07, F08). 확인: 0곳 조건 422, 진행 중인 뽑기가 있으면 409. 두 멤버가 조회한 후보가 같다.
  - 변경 파일: backend/app/schemas/draw.py, app/routers/draws.py(POST /groups/{group_id}/draws, GET .../draws/current, GET .../draws/{id}), app/main.py
  - 실행: 시험 스크립트(계정 3개, 새 그룹 3개), pytest, 서버 로그·DB 확인
  - 확인 결과 (2026-10-14): 28/28 통과. 0곳 조건(모든 카테고리 제외, 도보 1분) 422 NO_CANDIDATES이고 저장되지 않음. 중복·잘못된 카테고리, 가격대 0·4, 도보 61 422. 조건 뽑기 201: 후보 수 = min(3, 조건에 맞는 수), 중복 없음, 모두 조건 만족. 진행 중 뽑기가 있으면 409(0곳 조건이어도 409 먼저). 두 멤버의 current·상세 후보가 순서까지 같고 다시 조회해도 그대로. 멤버 아님·다른 그룹 경로·없는 id 404, 토큰 없음 401. 식당 2곳 그룹은 후보 2개. 동시 요청 5개 → 201 하나, 409 넷(서버 오류 0건). pytest 16 passed.
  - 남은 오류: 없음. 득표 수·내 표(T16), 결정·방문(T17), 평균 별점(T21)은 아직 0/null. 시험 그룹 "T14 뽑기팀"·"T14 소수팀"·"T14 동시팀"에 진행 중 뽑기가 남아 있음(마감은 T17).
- [x] T15: 뽑기 조건 화면과 DrawCard 뒤집기 컴포넌트를 구현한다. 확인: 카드를 누르면 뒤집히고, 모두 공개된 뒤에만 투표 버튼이 활성화된다. 0곳 조건에서는 안내 문구가 나온다.
  - 변경 파일: frontend/src/components/DrawSection.jsx(진행 중 뽑기 없으면 조건 폼, 있으면 카드·투표 버튼), components/DrawForm.jsx(제외 카테고리 칩, 최대 가격대, 최대 도보 시간, 0곳 안내, 409면 진행 중 뽑기 불러오기), components/DrawCard.jsx(누르면 3D 뒤집기, 움직임 줄이기 설정 시 애니메이션 없음), pages/GroupPage.jsx, App.css
  - 실행: npm run lint, npm run build
  - 확인 결과 (2026-10-14): lint 경고 0건, build 성공. 브라우저(사용자 확인, T08D 점심팀): 모든 카테고리를 빼고 뽑으면 '조건에 맞는 식당이 없어요' 안내. 뽑기 후 카드 3장이 뒤집힌 상태로 나오고 누르면 하나씩 공개, 모두 공개된 뒤에만 투표하기 버튼 활성.
  - 남은 오류: 없음. 투표하기는 아직 안내만 표시(T16·T18에서 연결). 카드 공개 상태는 화면별이라 새로고침하면 다시 덮임. T08D 점심팀에 진행 중 뽑기가 남아 있음.

## 5장: 투표와 결정
- [x] T16: votes, visits 모델과 PUT /draws/{id}/vote를 구현한다 (F10). 확인: 같은 멤버가 다시 투표하면 표 수는 그대로이고 선택만 바뀐다. 후보가 아닌 식당은 422, 마감 후 투표는 409.
  - 변경 파일: backend/app/models/vote.py(Vote: (session_id, member_id) UNIQUE, Visit: session_id UNIQUE), models/__init__.py, alembic/versions/1b3697f5aa41_create_votes_and_visits.py, schemas/draw.py(VoteIn), routers/draws.py(PUT .../draws/{id}/vote, 뽑기 객체에 vote_count·my_vote_restaurant_id)
  - 실행: alembic upgrade head, alembic check, 시험 스크립트, 동시 투표 부하 시험
  - 확인 결과 (2026-10-14): 20/20 통과. 같은 멤버가 다시 투표하면 총 표 수 1 그대로, 선택만 바뀌고 DB에 1행. 두 멤버가 보는 득표가 같고 current에도 반영. 후보가 아닌 식당·없는 id 422 NOT_A_CANDIDATE, 거절 후 득표 그대로. 마감 후 투표 409 DRAW_CLOSED(T14 소수팀 뽑기를 DB에서 CLOSED로 바꿔 재현)이고 저장되지 않음. 멤버 아님·다른 그룹 경로 404, 토큰 없음 401. 동시 투표 20개 → 모두 200, 멤버당 1행. 추가로 동시 40개 × 3회 모두 200, 득표 합계 2, 서버 오류 0건.
  - 남은 오류: 처음 구현(읽고 고치기)은 같은 멤버 동시 투표 6개 중 3개가 500(MariaDB 11.8 오류 1020 Record has changed since last read, innodb_snapshot_isolation=ON). INSERT ... ON DUPLICATE KEY UPDATE 한 문장으로 바꾸고 1020·1213이면 최대 3번 다시 시도하도록 수정함.
- [x] T17: POST /draws/{id}/close를 구현한다 (F11). 확인: 생성자가 아니면 403. 동점과 무투표일 때도 후보 중 하나로 결정된다. 두 번 호출해도 visits는 1건이고, visited_on은 한국 날짜다.
  - 변경 파일: backend/app/services/draw.py(decide: 최다 득표·동점·무투표 무작위, kst_date), tests/test_draw.py(7개 추가), app/routers/draws.py(POST .../draws/{id}/close, 뽑기 객체에 visit_id)
  - 실행: pytest, 시험 스크립트, 동시 마감 부하 시험
  - 확인 결과 (2026-10-14): pytest 23 passed(동점은 동점 후보만, 무투표는 전체 후보 모두 나올 수 있음, 후보 아닌 표 무시, 한국 자정 경계). 시험 21/21 통과: 생성자가 아니면 403(마감 후에도 403), 403 뒤 OPEN 유지. 동점(1:1) → 동점 후보 중 결정, 2표 받은 식당 → 그 식당, 무투표 → 후보 중 하나. visits 1건이고 visited_on = closed_at의 한국 날짜. 두 번 호출해도 같은 결과·visits 1건. 마감 후 투표 409, current null, A·B 결과 같음. 멤버 아님·다른 그룹 경로 404, 토큰 없음 401. 동시 마감 5개 모두 200·같은 결과·visits 1건, 추가로 10개 × 5회 모두 200, 서버 오류 0건. T16 동시 투표 30개 회귀 확인 200.
  - 남은 오류: 처음 구현은 동시 마감 5개 중 1개가 500(MariaDB 1020, 인증 때 잡힌 읽기 시점 이후에 행이 바뀜). 잠금 전에 트랜잭션을 새로 시작하고 1020·1213은 한 번 더 시도하도록 수정함. T16 시험 때 DB에서 직접 CLOSED로 바꾼 T14 소수팀의 뽑기 1건은 결정·방문 기록이 없는 시험 데이터로 남아 있음.
- [x] T18: usePolling 훅, 득표 표시, 마감 버튼, 결과 화면을 구현한다. 확인: 브라우저 3개에서 투표하면 3초 안에 다른 화면에 반영된다. 마감 결과가 세 화면에서 같다. 탭을 비활성화하면 개발자 도구에서 요청이 멈춘다.
  - 변경 파일: frontend/src/hooks/usePolling.js(요청이 끝난 뒤 3초 예약, 탭이 가려지면 멈추고 보이면 즉시 재개), components/DrawSection.jsx(조건 폼일 땐 current, 투표 중엔 draws/{id}를 3초마다 조회, 결과 화면에선 조회 안 함, 요청 순서 번호로 늦게 온 응답 무시, 후보별 득표 막대·투표 버튼, 생성자만 마감 버튼, 결과 화면), labels.js(decisionNote: 최다 득표·동점·무투표 안내), pages/GroupPage.jsx(my_member_id 전달), App.css
  - 실행: npm run lint, npm run build, node로 decisionNote 5가지 경우 확인, 세 번째 멤버(t08d_c)는 API 스크립트로 참여·투표
  - 확인 결과 (2026-10-14): lint 경고 0건, build 성공. 브라우저 2개(t08d_a 일반 창, t08d_b 시크릿 창) + API(t08d_c)로 3명 투표: 사용자 확인으로 다른 화면 득표가 3초 안에 반영. t08d_a가 마감 → 두 창의 결과와 t08d_c로 조회한 결과가 모두 '방콕 키친'(1:1:1 동점, 서버 무작위), visits 1건·visited_on 2026-10-14. 탭을 가리면 개발자 도구에서 요청이 멈추고 돌아오면 바로 재개(사용자 확인). 동점 안내 문구 추가(사용자 요청): 1:1:1 → '3곳이 1표로 동점이라 그중에서 무작위로 정했어요.' 등 5가지 경우 node로 확인.
  - 남은 오류: 없음. 마감 후 새로고침하면 진행 중 뽑기가 없어 조건 폼이 보임(지난 결과는 그 화면을 보던 동안에만 표시).

## 6장: 별점과 기록
- [x] T19: reviews 모델과 GET /visits/pending-review, POST /visits/{id}/reviews를 구현한다 (F12). 확인: 별점 0과 6은 422, 101자 한 줄 평은 422, 같은 방문의 두 번째 별점은 409.
  - 변경 파일: backend/app/models/review.py((visit_id, member_id) UNIQUE, rating 1~5 CHECK), models/__init__.py, alembic/versions/d2b50c2b8717_create_reviews.py, schemas/visit.py(별점은 strict 정수), routers/visits.py(GET .../visits/pending-review, POST .../visits/{id}/reviews), main.py
  - 실행: alembic upgrade head, alembic check, 시험 스크립트(중간에 스크립트의 시험 데이터 부족으로 멈춰 남은 항목을 이어서 실행), pytest
  - 확인 결과 (2026-10-14): 29/29 통과. 별점 0·6 422, 101자 한 줄 평 422, 같은 방문 두 번째 별점 409 ALREADY_REVIEWED(값은 첫 번째 그대로). 그 밖에 -1, 4.5, 4.0, "4", 누락, null 422이고 저장 안 됨. 100자 한 줄 평 201, 앞뒤 공백 제거, 생략 시 빈 문자열. 다른 멤버는 같은 방문에 별점 가능. 별점 남긴 방문은 내 대기 목록에서만 빠짐, 최근 방문부터 정렬. 같은 멤버 동시 8개 → 201 하나·409 일곱·DB 1건. 멤버 아님·다른 그룹 경로·없는 방문 404, 토큰 없음 401. 나중에 참여한 멤버의 대기 목록에는 참여 전 방문 없음. 서버 오류 0건, pytest 23 passed.
  - 남은 오류: 없음. T08D 점심팀의 방콕 키친 방문은 T20 화면 확인용으로 에이·비·씨 모두 대기 상태로 남겨 둠.
- [x] T20: 홈 화면의 평가 대기 카드와 별점 입력을 구현한다. 확인: 별점을 등록하면 평가 대기 목록에서 사라진다.
  - 변경 파일: frontend/src/components/PendingReviews.jsx(그룹 홈 맨 위 평가 대기 카드, 라디오 기반 별 5개, 한 줄 평 100자·글자 수, 등록 후 목록 다시 조회, 409면 카드 제거·안내, 비면 영역 숨김), components/DrawSection.jsx(마감 시 onDecided로 대기 목록 갱신), pages/GroupPage.jsx, App.css
  - 실행: npm run lint, npm run build, DB 조회
  - 확인 결과 (2026-10-14): lint 경고 0건, build 성공. 브라우저(사용자 확인, T08D 점심팀): 방콕 키친 평가 카드가 보이고 별점을 등록하면 평가 대기 목록에서 사라짐. DB에 비 5점·에이 4점 저장 확인.
  - 남은 오류: 없음
- [x] T21: 식당 상세 화면을 만들고 목록과 뽑기 카드에 평균 별점을 반영한다 (F13). 확인: 표시된 평균이 SQL AVG 결과를 소수 첫째 자리로 반올림한 값과 같다.
  - 변경 파일: backend/app/services/stats.py(식당별 ROUND(AVG(rating),1)·별점 수·최근 방문일), routers/restaurants.py(목록·등록·수정·상세에 통계, 상세에 방문 이력·한 줄 평), schemas/restaurant.py(VisitItem, ReviewItem), routers/draws.py·schemas/draw.py(후보 avg_rating), frontend/src/components/RestaurantDetail.jsx(상세 화면), components/RestaurantList.jsx(이름 누르면 상세), components/DrawCard.jsx·labels.js(카드는 평균만, 목록·상세는 '(N명)'), pages/GroupPage.jsx, App.css
  - 실행: 시험 스크립트(API 값과 SQL ROUND(AVG) 비교), npm run lint, npm run build, pytest
  - 확인 결과 (2026-10-14): 모든 그룹 식당 49곳의 avg_rating·review_count·last_visited_on이 SQL과 같음. 반올림 경계 5·4·3·1(AVG 3.2500) → 3.3. 상세의 방문 이력·한 줄 평 4개(닉네임·별점·내용) 일치, 방문 없는 식당은 visits []·평균 null. 별점 있는 후보가 들어간 뽑기에서 후보 평균 샐러드 데이 3.5·방콕 키친 3.3 = SQL. 브라우저(사용자 확인): T08D 점심팀 방콕 키친 ★ 4.5 (2명), T14 뽑기팀 방콕 키친 ★ 3.3 (4명)·샐러드 데이 ★ 3.5 (2명)가 SQL 값과 같고, 이름을 누르면 상세(방문 이력·별점·한 줄 평), 그룹 홈으로 돌아가기 동작. 서버 오류 0건, pytest 23 passed, lint 0건, build 성공.
  - 남은 오류: 없음. 시험 스크립트의 검사 2개가 제대로 검사하지 못해(항상 통과하는 식, 별점 없는 후보만 뽑힘) 별점 있는 후보로 다시 확인함. 시험 계정 t21_d(디) 추가, 시험용 뽑기 2건 마감.

## 6-1장: 화면 배치와 방문 여부 조건 (2026-10-14 사용자 요청으로 추가)
PC에서는 왼쪽에 그룹 목록을 둔 채 오른쪽에 그룹 화면을 보여 주고, 멤버는 칩으로 표시한다. 식당 목록과 뽑기 조건에 "가 본 곳/안 가 본 곳" 조건을 추가한다(F06, F07 수정).
- [x] T21A: PRD.md, API-SPEC.md, PLAN.md에 방문 여부 조건과 화면 배치를 반영한다. 확인: API-SPEC의 F01~F15가 모두 하나 이상의 API에 대응되고, 목록 쿼리 visited와 뽑기 filters.visited가 설명되어 있다.
  - 변경 파일: PRD.md(F06·F07에 방문 여부, 기술과 배포에 PC 좌우 배치·휴대폰 전환), API-SPEC.md(목록 쿼리 visited, 뽑기 filters.visited, 대응표 F06·F07, 정한 것 14: 가 본 식당 = 그 그룹에 방문 기록 1건 이상), PLAN.md(6-1장 T21A~T21C)
  - 확인 결과 (2026-10-14): 스크립트로 F01~F15 대응 통과(API 22개가 목록·상세에 모두 있음), visited 쿼리·filters.visited·정한 것 14 기재 확인.
  - 남은 오류: 없음
- [x] T21B: 768px 이상에서는 왼쪽 그룹 목록(만들기·참여 포함)과 오른쪽 그룹 화면을 나란히, 768px 미만에서는 목록과 그룹 화면을 오가게 한다. 그룹 멤버는 이름마다 칩으로 감싸고 본인 칩은 메인 색으로 표시한다. 확인: 1280px에서 그룹을 바꿔도 왼쪽 목록이 그대로 있고 선택한 그룹이 표시된다. 360px에서는 목록과 그룹 화면을 오간다. 멤버가 칩으로 보이고 본인 칩만 메인 색이다.
  - 변경 파일: frontend/src/App.jsx(로그인 후 workspace: 왼쪽 sidebar 그룹 목록 + 오른쪽 main-panel 그룹 화면, 미선택 시 안내), pages/GroupListPage.jsx(선택 그룹 강조, 만들기·참여 후 목록 다시 조회), pages/GroupPage.jsx(멤버 칩, 본인 칩 메인 색, 목록 버튼은 좁은 화면만), App.css(전체 폭 1200px, 768px 기준 grid 280px + 1fr, 좁은 화면은 선택 여부로 한쪽만 표시, 멤버 칩, 쓰지 않는 .member-list 삭제)
  - 실행: npm run lint, npm run build
  - 확인 결과 (2026-10-14): lint 경고 0건, build 성공. 브라우저(사용자 확인, t08d_b): 1280px에서 그룹을 바꿔도 왼쪽 목록이 그대로이고 선택한 그룹이 오른쪽에 표시. 360px에서는 목록과 그룹 화면을 오감. 멤버가 칩으로 보이고 본인 칩만 메인 색.
  - 남은 오류: 없음
- [x] T21C: 식당 목록 API에 visited 쿼리, 뽑기에 filters.visited를 추가하고 화면에 방문 여부 선택을 넣는다 (F06, F07). 확인: visited=true와 visited=false의 결과 수가 같은 조건의 SQL 결과와 같고 둘의 합이 전체와 같다. 안 가 본 곳만 뽑으면 방문 기록이 있는 식당이 후보에 없고, 0곳이면 422. 추첨 함수 pytest를 추가한다.
  - 변경 파일: backend/app/services/draw.py(DrawFilters.visited, matches·eligible·pick_candidates에 visited_ids), schemas/draw.py(visited: StrictBool | None, DrawFiltersOut.visited), routers/draws.py(그룹 방문 식당 id를 추첨에 전달), routers/restaurants.py(목록 visited 쿼리, EXISTS), tests/test_draw.py(7개 추가), frontend/src/labels.js(VISITED_OPTIONS), components/RestaurantList.jsx(방문 여부 선택), components/DrawForm.jsx(방문 여부 칩), App.css
  - 실행: pytest, 시험 스크립트(API 결과 수와 EXISTS 기반 SQL COUNT 비교, 뽑기 반복), npm run lint, npm run build
  - 확인 결과 (2026-10-14): pytest 30 passed. 시험 20/20 통과: 그룹 4개 모두 visited=true·false 결과 수 = SQL이고 합 = 전체, 카테고리와 함께 6조합도 SQL과 같음, visited=abc 422. 안 가 본 곳만 8번 뽑기에서 방문 기록 있는 식당이 후보에 0번(후보 12곳), filters.visited=false 저장. 가 본 곳만 뽑기 후보는 모두 방문 식당. 방문 기록 없는 새 그룹에서 가 본 곳만 → 422 NO_CANDIDATES이고 저장 안 됨. visited "yes"·1·"true" 422. 서버 오류 0건. 브라우저(사용자 확인, T08D 점심팀): 목록 가 본 곳 1곳·안 가 본 곳 16곳, 뽑기 방문 여부 칩 동작.
  - 남은 오류: 없음. 시험으로 T14 뽑기팀에 마감된 뽑기·방문 기록이 늘었고, 시험 그룹 "T21C 새팀"을 만듦.

## 6-2장: 실제로 갔는지 응답 (2026-10-14 사용자 요청으로 추가)
투표로 정해지고 실제로는 안 간 경우를 구분한다. 멤버마다 별점(갔어요) 또는 "안 갔어요"로 1회 응답하고, 별점이 1개 이상 있는 방문만 실제 방문으로 센다(F06, F07, F12, F13 수정).
- [x] T21D: PRD.md, API-SPEC.md, PLAN.md에 "안 갔어요" 응답과 실제 방문 기준을 반영한다. 확인: API-SPEC의 F01~F15가 모두 하나 이상의 API에 대응되고, skip API·ALREADY_RESPONDED·실제 방문 규칙이 설명되어 있다.
  - 변경 파일: PRD.md(F06 가 본 곳 = 실제 방문, F12 갔어요/안 갔어요 1회 응답, F13 실제 방문 이력, 완료 기준), API-SPEC.md(ALREADY_RESPONDED, POST .../visits/{id}/skip, 실제 방문 규칙, 정한 것 14 수정·15·16 추가), PLAN.md(6-2장 T21D~T21F)
  - 확인 결과 (2026-10-14): 스크립트로 F01~F15 대응 통과(API 23개가 목록·상세에 모두 있음), skip API·ALREADY_RESPONDED·실제 방문 규칙 기재 확인.
  - 남은 오류: 없음
- [x] T21E: visit_skips 모델·마이그레이션과 POST /groups/{group_id}/visits/{id}/skip을 구현하고, 응답 대기 목록·가 본 곳(목록 visited, 뽑기 filters.visited)·최근 방문일·방문 이력을 실제 방문 기준으로 바꾼다. 확인: 안 갔어요 201 후 응답 대기 목록에서 빠짐, 안 갔어요 뒤 별점·별점 뒤 안 갔어요·안 갔어요 두 번은 409. 별점 없는 방문만 있는 식당은 가 본 곳·최근 방문일·방문 이력에 나오지 않고, 별점이 생기면 나온다. 결과가 같은 조건의 SQL과 같다.
  - 변경 파일: backend/app/models/review.py(VisitSkip, (visit_id, member_id) UNIQUE), models/__init__.py, alembic/versions/fac770213e61_create_visit_skips.py, services/stats.py(IS_REAL_VISIT, real_visited_restaurant_ids, 최근 방문일은 실제 방문만), routers/visits.py(POST .../skip, 별점·안 갔어요를 방문 행 잠금으로 직렬화, 응답 대기는 별점·안 갔어요 모두 제외), routers/restaurants.py(목록 visited·상세 방문 이력은 실제 방문만), routers/draws.py(filters.visited는 실제 방문 기준), schemas/visit.py(SkipOut)
  - 실행: alembic upgrade head, alembic check, 시험 스크립트(새 그룹 T21E 응답팀), 동시 응답 반복 시험, pytest
  - 확인 결과 (2026-10-14): 27/27 통과. 응답 전 별점 없는 방문은 가 본 곳·최근 방문일·방문 이력에 없음. 안 갔어요 201 → 그 사람 응답 대기에서만 빠짐. 안 갔어요 두 번·안 갔어요 뒤 별점·별점 뒤 안 갔어요 409 ALREADY_RESPONDED, 별점 두 번 409 ALREADY_REVIEWED. 별점이 생기면 가 본 곳·최근 방문일·방문 이력 1건으로 나옴. 세 명 모두 안 갔어요면 끝까지 안 나옴. 뽑기 안 가 본 곳만에서 실제 방문 식당 제외·가 본 곳만은 그 식당만. 그룹 6개 모두 목록 visited 결과 수 = 실제 방문 기준 SQL. 같은 멤버 별점·안 갔어요 동시 10개 → 201 하나·DB 1건, 두 멤버 동시 16개 × 3회 → 멤버당 201 하나·DB 2건. 없는 방문·다른 그룹 경로·멤버 아님 404, 토큰 없음 401. 서버 오류 0건, pytest 30 passed.
  - 남은 오류: 처음 구현은 잠그기 전에 만료된 member 값을 읽어 읽기 시점이 잠금보다 먼저 잡힐 수 있었음(동시 요청 때 별점과 안 갔어요가 둘 다 저장될 위험). 필요한 id를 commit 전에 꺼내도록 고친 뒤 시험함. 기존 시험 데이터 중 별점 없는 방문(T14 뽑기팀 8건 등)은 이제 가 본 곳에서 빠짐(새 규칙대로). 시험 중 만든 뽑기 7건의 방문 기록은 다음 회차에 영향이 없게 지움.
- [x] T21F: 별점 카드에 "안 갔어요" 버튼(확인 창 포함)을 넣는다. 확인: 안 갔어요를 누르고 확인하면 카드가 사라지고, 취소하면 그대로다. 그 식당이 목록의 가 본 곳에 나오지 않는다.
  - 변경 파일: frontend/src/components/PendingReviews.jsx(안 갔어요 버튼·확인 창, 409면 카드 제거), App.css
  - 확인 결과 (2026-10-15, 배포된 사이트를 headless Chromium으로 조작): lint 0건·build 성공. 별점 카드에서 안 갔어요 → 확인 창 취소하면 카드 그대로, 확인하면 카드가 사라지고 안내 문구 표시. 그 식당은 목록 '가 본 곳'에 없음.
  - 남은 오류: 없음. 첫 시도는 시험 스크립트가 카드가 사라지기 전에 개수를 세어 실패로 나와, 사라질 때까지 기다리게 고쳐 다시 확인함.

## 7장: 마무리와 시연 배포
- [x] T22: 다시 뽑기를 구현한다 (F09). 확인: 직전 후보가 제외되고 기존 투표가 초기화된다. 두 번째 요청은 409, 생성자가 아니면 403.
  - 변경 파일: backend/app/routers/draws.py(POST .../draws/{id}/redraw, 뽑기 행 잠금·재시도), frontend/src/components/DrawSection.jsx(생성자에게 다시 뽑기 (1회) 버튼), App.css
  - 확인 결과: API 10/10 통과(2026-10-14). 직전 후보와 겹치지 않는 2라운드 후보, 투표 초기화(득표 0·DB 0행), 두 번째 요청 409 REDRAW_ALREADY_USED, 생성자가 아니면 403, 1라운드 후보 투표 422, 마감은 2라운드 후보 중 결정, 마감 후 409 DRAW_CLOSED, 남는 식당이 없으면 422이고 그대로, 동시 5개 → 200 하나. 화면(2026-10-15, headless Chromium): 다시 뽑기 (1회) → 후보가 겹치지 않게 바뀜(가게 D·C·F → B·E·G), 카드가 다시 덮이고 버튼이 사라지며 다른 멤버의 표가 초기화됨.
  - 남은 오류: 없음
- [x] T23: 768px 기준 반응형 레이아웃과 로딩·오류 표시를 적용한다. 확인: 개발자 도구에서 360px은 1열·세로 카드, 1280px은 3열 목록·가로 카드. API를 중지하면 오류가 표시된다.
  - 변경 파일: frontend/src/App.css(식당 목록 1·2·3열, 휴대폰 뽑기 카드 세로 쌓기, 로딩 회전 표시), api.js(JSON이 아닌 5xx는 '서버에 연결할 수 없어요'), 각 화면의 로딩 문구에 loading 클래스
  - 확인 결과 (2026-10-15, headless Chromium): 1280px에서 식당 목록 3열, 뽑기 카드 3장이 같은 줄에 가로로 나란히(x 377·656·936, y 517). 360px에서 그룹 목록 숨김, 식당 목록 1열, 뽑기 카드 세로로 쌓임, 가로 스크롤 없음. API가 502를 주면 '서버에 연결할 수 없어요' 표시(Nginx와 같은 HTML 502로 가로채 확인, 실제로 API를 강제 종료하면 Nginx가 502를 주는 것도 확인). 1280px 사진에서 꺼진 투표 버튼과 마감 버튼이 붙어 보여 간격 8px 추가.
  - 남은 오류: 없음. 간격 수정은 배포 서버에 반영하려면 bash deploy/deploy.sh를 다시 실행해야 함.
- [x] T24: 프론트엔드를 빌드하고 Nginx로 정적 파일과 /api 프록시를 구성한다. FastAPI는 systemd(lunch-api)로 등록한다. 확인: 서버 주소로 휴대폰과 PC에서 접속해 뽑기, 투표, 결정, 별점을 끝까지 수행한다. FastAPI를 재시작해도 데이터가 유지된다. 외부에서 3306과 8000 포트에 접속되지 않는다.
  - 변경 파일: deploy/nginx-lunch.conf(80번 기본 서버, /var/www/lunch, /api → 127.0.0.1:8000), deploy/lunch-api.service(127.0.0.1:8000, workers 2), deploy/deploy.sh(빌드·복사·마이그레이션·서비스·Nginx 교체)
  - 확인 결과 (2026-10-15): 사용자가 deploy.sh 실행(lunch-api·nginx active, sites-enabled에는 lunch만, /var/www/lunch). ngrok 공개 주소(https://floral-example-semester.ngrok-free.dev)로 PC 화면(1280px, 에이)과 휴대폰 화면(iPhone 13 에뮬레이션, 비)에서 카드 공개 → 투표(PC에 2표 반영 1.8초) → 마감(두 화면 결과 같음) → 별점 5·4점 → 평균 4.5까지 수행. lunch-api를 SIGKILL로 강제 종료 → systemd가 자동 재시작(NRestarts 0→1), 계정 10·식당 88·방문 39·별점 17·안 갔어요 9로 그대로. 3306·8000은 127.0.0.1에서만 열려 외부 주소(172.28.103.151)로 접속 안 됨, 80만 접속됨.
  - 남은 오류: 실제 휴대폰 기기 대신 Chromium 휴대폰 에뮬레이션으로 확인함. systemctl restart는 sudo가 필요해 강제 종료 후 자동 재시작으로 확인함.
- [x] T25: README.md에 설치와 실행 방법을 정리한다. 확인: 새 폴더에 저장소를 받아 README 순서대로 실행하면 health가 ok를 반환한다.
  - 변경 파일: README.md
  - 확인 결과 (2026-10-14): 새 폴더에 git clone 후 README 순서대로 venv·pip install·alembic upgrade head·uvicorn(8100번) 실행 → health {"status":"ok","db":"ok"}. 같은 폴더에서 pytest 30 passed, npm ci·lint·build 성공. DB 생성(sudo)은 이미 있는 DB라 .env 복사로 대신함. 확인용 폴더는 .env가 있어 삭제.
  - 남은 오류: 없음

## 8장: EC2 3티어 배포 (2026-10-15 사용자 요청으로 추가)
WSL 한 대에서 돌던 구조를 EC2 3대(front: 퍼블릭 서브넷, back: 프라이빗 서브넷 1, db: 프라이빗 서브넷 2)로 나눈다. VPC, 서브넷, NAT 게이트웨이, SSM 접속은 사용자가 준비해 두었다. 보안 그룹 설정과 EC2 안의 sudo 명령은 사용자가 실행하고, 결과를 받아 기록한다. 각 서버는 공개 저장소를 git clone 해서 쓴다. WSL의 기존 DB 데이터는 옮기지 않고, db 서버에는 빈 DB를 만들어 마이그레이션한다.
- [x] T26: PRD.md와 PLAN.md에 EC2 3티어 배포 구조를 반영한다. 확인: PRD의 기술과 배포·완료 기준에 서버 3대의 서브넷, 허용 포트, DB 사용자 접속 범위가 적혀 있고, PLAN에 서버별 작업과 확인 방법이 있다.
  - 변경 파일: PRD.md(기술과 배포, 완료 기준), PLAN.md(8장, 실행 기준)
  - 확인 결과 (2026-10-15): PRD 기술과 배포에 front 퍼블릭·back 프라이빗 1·db 프라이빗 2, 80/8000/3306 허용 방향, 보안 그룹 ID 기준, SSM·NAT, back 사설 IP 전용 DB 사용자를 기록함. 완료 기준에 3티어 접속 차단 조건을 추가함. API-SPEC은 API 계약이 바뀌지 않아 수정하지 않음.
  - 남은 오류: 없음
- [ ] T27: 배포 파일을 서버별로 나눈다. Nginx 설정의 /api 대상(back 주소)과 lunch-api 서비스의 수신 주소를 설치할 때 넣는 값으로 바꾸고, back 서비스에서 mariadb.service 의존을 뺀다. front용·back용 배포 스크립트와 db 생성 SQL 안내를 만들고, 기존 deploy.sh(WSL 한 대 배포)는 그대로 동작하게 둔다. 확인: bash -n으로 스크립트 문법 검사. back 주소를 넣어 만든 Nginx 설정이 nginx -t를 통과한다. WSL에서 deploy.sh로 다시 배포해도 health가 ok다.
  - 변경 파일: deploy/nginx-lunch.conf(proxy_pass 대상 __API_UPSTREAM__), deploy/lunch-api.service(수신 주소 __API_HOST__, DB 의존 __DB_UNIT__, network-online.target 뒤에 시작), deploy/deploy.sh(127.0.0.1:8000, 127.0.0.1, mariadb.service로 치환), deploy/deploy-db.sh(새 파일: lunch DB와 lunch_app@<back 사설 IP> 생성, bind-address 확인), deploy/deploy-back.sh(새 파일: venv·마이그레이션·0.0.0.0:8000 서비스), deploy/deploy-front.sh(새 파일: Node 버전 확인·빌드·/api → <back 사설 IP>:8000 Nginx)
  - 확인 결과 (2026-10-15): 스크립트 4개 bash -n 통과. 잘못된 IP 인자와 12자 미만·따옴표 포함 비밀번호는 사용법 안내 후 종료. Node 버전 검사는 v20.19·v22.12·v24 통과, v18·v20.0·v21·v22.11 거절. back 주소(10.0.2.15)를 넣은 Nginx 설정은 nginx -t 통과(일반 사용자라 80번 대신 8088번으로 바꿔 검사). WSL용으로 치환한 Nginx 설정은 설치된 /etc/nginx/sites-available/lunch와 주석 외 동일. 치환한 서비스 파일 2종(WSL, EC2)은 systemd-analyze verify 오류 없음. WSL용은 설치된 파일과 After/Wants의 network-online.target만 다름.
  - 추가 (2026-10-15): EC2가 Amazon Linux(ec2-user)라 deploy-back.sh는 Python 3.12 이상(python3.13·3.12·python3 순)을 찾고 3.12 미만 .venv는 안내 후 멈추게, deploy-front.sh는 nginx·rsync·curl 유무 확인, sites-available이 없으면 /etc/nginx/conf.d/lunch.conf에 설치, systemctl enable --now nginx를 하게 고침. deploy-db.sh 안내에 Amazon Linux 설정 경로와 nc 대신 /dev/tcp 확인을 넣음. 확인: bash -n 통과, Amazon Linux 기본 서버(server_name _, default_server 없음)와 함께 넣은 설정이 nginx -t 통과(server_name 충돌 경고만, 요청은 default_server인 이 설정이 받음).
  - 남은 오류: WSL에서 deploy.sh 재배포 후 health 확인은 sudo가 필요해 사용자 실행 대기.
- [ ] T28: db 서버에 MariaDB를 설치하고 bind-address를 사설 IP로 열고, lunch DB와 lunch_app@<back 사설 IP> 사용자를 만든다. 보안 그룹은 3306번을 back 보안 그룹에서만 허용한다. 확인: back에서 nc -zv <db 사설 IP> 3306 성공, front에서는 실패. back에서 lunch_app으로 접속해 SELECT 1.
- [ ] T29: back 서버에 저장소를 clone 하고 backend/.env(DB_HOST=db 사설 IP, 권한 600)를 만든 뒤 venv 설치, alembic upgrade head, lunch-api 서비스(0.0.0.0:8000)를 등록한다. 보안 그룹은 8000번을 front 보안 그룹에서만 허용한다. 확인: back에서 curl 127.0.0.1:8000/api/v1/health가 status=ok, db=ok. front에서 curl <back 사설 IP>:8000/api/v1/health도 같은 결과.
- [ ] T30: front 서버에 저장소를 clone 하고 화면을 빌드해 /var/www/lunch에 복사한 뒤, /api를 back 사설 IP로 넘기는 Nginx 설정을 켠다. 보안 그룹은 80번만 외부에 연다. 확인: front에서 curl 127.0.0.1/api/v1/health가 ok. 휴대폰과 PC에서 front 공인 IP로 회원가입, 그룹, 뽑기, 투표, 마감, 별점을 끝까지 수행한다. lunch-api를 재시작해도 데이터가 유지된다. back과 db에 공인 IP가 없다.
- [ ] T31: README.md에 EC2 3티어 배포 방법(서버별 순서, 보안 그룹, 확인 명령)을 추가한다. 확인: README 순서대로 front·back·db 서버를 설정하면 health가 ok를 반환한다.

## 실행 기준
T01: sudo mariadb
T02~T22 백엔드: backend 폴더의 가상환경에서 python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
T03~T23 프론트엔드: frontend 폴더에서 npm run dev -- --host 127.0.0.1 --port 5173
T05 이후 마이그레이션: backend 폴더에서 alembic revision --autogenerate -m "<내용>" 후 alembic upgrade head
T24: npm run build, sudo nginx -t, sudo systemctl reload nginx, sudo systemctl restart lunch-api
T28~T30: 각 EC2에 SSM으로 접속해 실행한다. db는 sudo mariadb, back은 backend 폴더의 .venv와 sudo systemctl restart lunch-api, front는 npm run build와 sudo nginx -t, sudo systemctl reload nginx
실제로 존재하는 파일과 폴더를 확인한 뒤 명령을 실행한다.

## 기록
각 작업마다 변경 파일, 실행 명령, 실제 확인 결과, 남은 오류를 기록한다. 정상 동작을 확인한 작업 단위로 Git 커밋한다.
