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
