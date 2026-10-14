# 오늘 뭐 먹지? API 명세

PRD.md의 F01~F15를 구현하는 HTTP API 계약이다. 구현 순서는 PLAN.md를 따르고, 이 문서와 구현이 다르면 구현 전에 이 문서를 먼저 고친다.

## 공통 규칙

### 주소
- 모든 경로 앞에 `/api/v1`이 붙는다. 아래 표와 예시는 이를 생략한다.
- 요청·응답 본문은 JSON(UTF-8)이다.
- 그룹 안의 데이터(식당, 뽑기, 방문, 별점)는 `/groups/{group_id}/...` 아래에 둔다. 한 계정이 여러 그룹에 속하기 때문에 어느 그룹의 데이터인지 경로로 정한다.

### 인증
- 회원가입·로그인 응답의 `token`(세션 토큰)을 브라우저 localStorage(`lunch-token-v1`)에 저장한다.
- 인증이 필요한 요청은 헤더에 토큰을 보낸다.
  ```
  Authorization: Bearer <token>
  ```
- 인증 없이 호출하는 API: `GET /health`, `POST /auth/signup`, `POST /auth/login`. 나머지는 모두 토큰이 필요하다.
- 세션 토큰은 발급 후 30일 동안 유효하다. 로그아웃하거나 기간이 지나면 401이다.
- `/groups/{group_id}/...` 요청은 서버가 "로그인한 계정이 그 그룹의 멤버인지" 확인한다. 멤버가 아니면 404다.

### 식별자와 시각
- 수정, 삭제, 투표, 별점은 화면 순번이 아니라 고유 `id`로 요청한다.
- 그룹 안에서 사람을 가리키는 `member`/`created_by`의 `id`는 그 그룹의 멤버 id(`members.id`)이고, `nickname`은 계정의 닉네임이다.
- 시각(`*_at`)은 UTC ISO 8601 문자열이다. 예: `"2026-10-14T03:20:00Z"`. 화면에서 한국 시간으로 바꿔 표시한다.
- 날짜(`visited_on`)는 한국 시간 기준 `"YYYY-MM-DD"`이다.

### 입력 정리
- 그룹명, 닉네임, 식당 이름, 한 줄 평은 앞뒤 공백을 제거한 뒤 길이를 검사한다.
- 아이디는 앞뒤 공백을 제거하고 소문자로 바꾼 뒤 검사한다. 비밀번호는 공백을 포함해 그대로 쓴다.
- 초대 코드는 앞뒤 공백을 제거하고 대문자로 바꾼 뒤 비교한다.
- 서버는 사용자 입력을 그대로 저장하고 그대로 돌려준다. 화면은 이를 HTML로 실행하지 않고 글자로 표시한다.

### 오류 응답

| 코드 | 의미 | 대표 상황 |
|---|---|---|
| 401 | 인증 실패 | 토큰이 없거나 맞지 않음, 로그아웃·만료된 토큰, 로그인 실패 |
| 403 | 권한 없음 | 뽑기를 만들지 않은 멤버가 마감·다시 뽑기 요청 |
| 404 | 찾을 수 없음 | 없는 초대 코드, 없는 id, **내가 멤버가 아닌 그룹과 그 데이터**, 삭제된 식당 |
| 409 | 현재 상태와 충돌 | 중복 아이디·닉네임, 이미 참여한 그룹, 진행 중인 뽑기 있음, 마감 후 투표, 다시 뽑기 2회째, 같은 방문에 두 번째 별점 |
| 422 | 입력값 오류 | 길이·범위·형식 위반, 조건에 맞는 식당 0곳, 후보가 아닌 식당에 투표 |

내가 멤버가 아닌 그룹의 데이터는 403이 아니라 404로 응답해 존재 여부를 알려 주지 않는다.

오류 본문은 두 가지 형태다.

- 형식 검증 실패 (422, FastAPI 기본 형식)
  ```json
  { "detail": [ { "loc": ["body", "name"], "msg": "String should have at least 1 character", "type": "string_too_short" } ] }
  ```
- 그 밖의 모든 오류 (401, 403, 404, 409, 업무 규칙 422)
  ```json
  { "detail": { "code": "DUPLICATE_NICKNAME", "message": "이미 사용 중인 닉네임입니다." } }
  ```

화면은 `detail`이 배열이면 입력 오류로, 객체이면 `code`로 상황을 구분한다.

| code | 상태 | 설명 |
|---|---|---|
| `UNAUTHORIZED` | 401 | 토큰 없음, 잘못된 토큰, 로그아웃·만료된 토큰 |
| `INVALID_CREDENTIALS` | 401 | 로그인 실패 (아이디와 비밀번호 중 무엇이 틀렸는지 구분하지 않음) |
| `NOT_DRAW_CREATOR` | 403 | 뽑기를 만든 멤버만 할 수 있는 요청 |
| `GROUP_NOT_FOUND` | 404 | 초대 코드에 해당하는 그룹 없음, 또는 내가 멤버가 아닌 그룹 |
| `RESTAURANT_NOT_FOUND` | 404 | 식당 없음, 다른 그룹, 삭제됨 |
| `DRAW_NOT_FOUND` | 404 | 뽑기 없음 또는 다른 그룹 |
| `VISIT_NOT_FOUND` | 404 | 방문 기록 없음 또는 다른 그룹 |
| `DUPLICATE_LOGIN_ID` | 409 | 이미 사용 중인 아이디 |
| `DUPLICATE_NICKNAME` | 409 | 이미 사용 중인 닉네임 (전체 서비스 기준) |
| `ALREADY_MEMBER` | 409 | 이미 참여한 그룹 |
| `ACTIVE_DRAW_EXISTS` | 409 | 그룹에 진행 중인 뽑기가 이미 있음 |
| `DRAW_CLOSED` | 409 | 마감된 뽑기에 투표·다시 뽑기 |
| `REDRAW_ALREADY_USED` | 409 | 다시 뽑기를 이미 사용함 |
| `ALREADY_REVIEWED` | 409 | 같은 방문에 이미 별점을 남김 |
| `NO_CANDIDATES` | 422 | 조건에 맞는 식당이 0곳 |
| `NOT_A_CANDIDATE` | 422 | 현재 후보가 아닌 식당에 투표 |

## 엔드포인트 목록

`{gid}`는 `{group_id}`의 줄임이다.

| 메서드 | 경로 | 인증 | 설명 | PRD | PLAN |
|---|---|---|---|---|---|
| GET | `/health` | - | 서버와 DB 상태 | - | T02 |
| POST | `/auth/signup` | - | 회원가입 + 로그인 | F14 | T08C |
| POST | `/auth/login` | - | 로그인 | F15 | T08C |
| POST | `/auth/logout` | ✓ | 로그아웃 (현재 토큰 무효화) | F15 | T08C |
| GET | `/me` | ✓ | 내 계정 정보 | F15 | T08C |
| GET | `/groups` | ✓ | 내가 속한 그룹 목록 | F02 | T08D |
| POST | `/groups` | ✓ | 그룹 생성 + 첫 멤버 등록 | F01 | T08D |
| POST | `/groups/join` | ✓ | 초대 코드로 참여 | F02 | T08D |
| GET | `/groups/{gid}` | ✓ | 그룹 정보와 멤버 목록 | F02 | T08D |
| GET | `/groups/{gid}/restaurants` | ✓ | 식당 목록, 검색·필터 | F06 | T09, T11 |
| POST | `/groups/{gid}/restaurants` | ✓ | 식당 등록 | F03, F04 | T09 |
| GET | `/groups/{gid}/restaurants/{id}` | ✓ | 식당 상세 (평균 별점, 방문 이력, 한 줄 평) | F13 | T09, T21 |
| PATCH | `/groups/{gid}/restaurants/{id}` | ✓ | 식당 수정 (보낸 필드만) | F03, F04 | T09 |
| DELETE | `/groups/{gid}/restaurants/{id}` | ✓ | 식당 삭제 (소프트 삭제) | F05 | T09 |
| POST | `/groups/{gid}/draws` | ✓ | 카드 뽑기 시작 | F07, F08 | T14 |
| GET | `/groups/{gid}/draws/current` | ✓ | 진행 중인 뽑기 | F08, F10 | T14 |
| GET | `/groups/{gid}/draws/{id}` | ✓ | 뽑기 상세 (후보, 득표, 결과) | F08, F10, F11 | T14 |
| POST | `/groups/{gid}/draws/{id}/redraw` | ✓ | 다시 뽑기 | F09 | T22 |
| PUT | `/groups/{gid}/draws/{id}/vote` | ✓ | 투표 또는 표 변경 | F10 | T16 |
| POST | `/groups/{gid}/draws/{id}/close` | ✓ | 마감과 결정 | F11 | T17 |
| GET | `/groups/{gid}/visits/pending-review` | ✓ | 내가 아직 평가하지 않은 방문 | F12 | T19 |
| POST | `/groups/{gid}/visits/{id}/reviews` | ✓ | 별점과 한 줄 평 등록 | F12 | T19 |

---

## 상태 확인

### GET /health
DB에 `SELECT 1`을 실행해 상태를 돌려준다.

- `200` `{ "status": "ok", "db": "ok" }`
- `503` `{ "status": "error", "db": "error" }`

---

## 계정

### 계정 객체
```json
{ "id": 3, "login_id": "minji_01", "nickname": "민지", "created_at": "2026-10-14T03:00:00Z" }
```

### POST /auth/signup (F14)
계정을 만들고 바로 로그인 상태로 만든다.

요청
```json
{ "login_id": "Minji_01", "password": "lunch-2026!", "nickname": "민지" }
```

| 필드 | 규칙 |
|---|---|
| `login_id` | 필수, 공백 제거·소문자 변환 후 영문 소문자·숫자·밑줄 4~20자, 중복 불가 |
| `password` | 필수, 8~64자 |
| `nickname` | 필수, 공백 제거 후 1~20자, 전체 서비스에서 중복 불가 |

응답 `201`
```json
{
  "token": "q9X2...(서버가 만든 무작위 문자열)",
  "user": { "id": 3, "login_id": "minji_01", "nickname": "민지", "created_at": "2026-10-14T03:00:00Z" }
}
```
- 비밀번호는 응답에 포함하지 않고, DB에는 해시만 저장한다.
- DB에는 토큰 원문 대신 해시를 저장한다.

오류
- `409 DUPLICATE_LOGIN_ID`, `409 DUPLICATE_NICKNAME`
- `422`: 아이디 형식·길이, 비밀번호 길이, 빈 닉네임·길이 초과

### POST /auth/login (F15)
요청
```json
{ "login_id": "minji_01", "password": "lunch-2026!" }
```

응답 `200`: `POST /auth/signup`과 같은 형식이다. 로그인할 때마다 새 토큰을 발급하므로 여러 기기에서 동시에 로그인할 수 있다.

오류
- `401 INVALID_CREDENTIALS`: 없는 아이디 또는 틀린 비밀번호 (구분하지 않음)
- `422`: 빈 아이디·비밀번호

### POST /auth/logout (F15)
지금 요청에 쓴 토큰만 무효화한다. 다른 기기의 로그인은 유지된다.

요청 본문 없음

응답 `204` (본문 없음)

오류: `401 UNAUTHORIZED`

### GET /me (F15)
저장된 토큰이 유효한지 확인하고 내 계정 정보를 돌려준다. 화면은 새로고침할 때 이 API로 로그인 상태를 복원한다.

응답 `200`
```json
{ "user": { "id": 3, "login_id": "minji_01", "nickname": "민지", "created_at": "2026-10-14T03:00:00Z" } }
```

오류: `401 UNAUTHORIZED` (화면은 저장된 토큰을 지우고 로그인 화면으로 이동한다)

---

## 그룹과 멤버

### 그룹 객체
```json
{ "id": 1, "name": "개발팀 점심", "invite_code": "K7Q2MZ", "member_count": 4, "my_member_id": 7, "joined_at": "2026-10-14T03:05:00Z" }
```
- `my_member_id`: 이 그룹에서 내 멤버 id. 뽑기 생성자 비교 등에 쓴다.
- `joined_at`: 내가 이 그룹에 참여한 시각.

### GET /groups (F02)
내가 속한 그룹 목록이다. 최근에 참여한 그룹부터 정렬한다.

응답 `200`
```json
{ "items": [ { "id": 1, "name": "개발팀 점심", "...": "그룹 객체" } ] }
```

### POST /groups (F01)
그룹을 만들고, 나를 첫 멤버로 등록한다.

요청
```json
{ "group_name": "개발팀 점심" }
```

| 필드 | 규칙 |
|---|---|
| `group_name` | 필수, 공백 제거 후 1~30자 |

응답 `201`: 그룹 객체
- `invite_code`는 영문 대문자와 숫자로 된 6자리이며 그룹마다 다르다. 겹치면 서버가 다시 만든다.

오류: `422` 빈 그룹명, 길이 초과

### POST /groups/join (F02)
초대 코드로 그룹에 참여한다. 그룹 안에서는 계정의 닉네임으로 표시된다.

요청
```json
{ "invite_code": "k7q2mz" }
```

| 필드 | 규칙 |
|---|---|
| `invite_code` | 필수, 공백 제거·대문자 변환 후 비교 |

응답 `201`: 참여한 그룹의 그룹 객체

오류
- `404 GROUP_NOT_FOUND`: 없는 초대 코드
- `409 ALREADY_MEMBER`: 이미 참여한 그룹
- `422`: 빈 초대 코드

### GET /groups/{group_id} (F02)
그룹 정보와 멤버 목록이다. 그룹 화면에 들어갈 때 호출한다.

응답 `200`
```json
{
  "id": 1, "name": "개발팀 점심", "invite_code": "K7Q2MZ", "member_count": 2, "my_member_id": 7, "joined_at": "2026-10-14T03:05:00Z",
  "members": [ { "id": 7, "nickname": "민지" }, { "id": 9, "nickname": "준호" } ]
}
```
- `members`는 참여한 순서로 정렬한다.

오류: `404 GROUP_NOT_FOUND` (없는 그룹 또는 내가 멤버가 아닌 그룹)

---

## 식당

### 식당 객체
목록, 등록, 수정 응답에 공통으로 쓴다.

```json
{
  "id": 12,
  "name": "할머니 순대국",
  "category": "KOREAN",
  "price_level": 1,
  "walk_minutes": 7,
  "map_url": "https://map.example.com/place/123",
  "memo": "11시 50분 전에 가야 자리 있음",
  "created_by": { "id": 1, "nickname": "민지" },
  "created_at": "2026-10-14T03:20:00Z",
  "avg_rating": 4.3,
  "review_count": 6,
  "last_visited_on": "2026-10-10"
}
```

| 필드 | 규칙 | 기본값 |
|---|---|---|
| `name` | 필수, 공백 제거 후 1~50자 | - |
| `category` | 필수, `KOREAN`, `CHINESE`, `JAPANESE`, `WESTERN`, `SNACK`, `ASIAN`, `ETC` 중 하나 | - |
| `price_level` | 1(1만 원 이하), 2(1~1.5만 원), 3(1.5만 원 초과) | 2 |
| `walk_minutes` | 0~60 정수 또는 `null` | `null` |
| `map_url` | `http://` 또는 `https://`로 시작하는 URL, 최대 500자, 또는 `null` | `null` |
| `memo` | 최대 200자 | `""` |
| `avg_rating` | 이 식당의 모든 별점 평균, 소수 첫째 자리 반올림. 별점이 없으면 `null` | 읽기 전용 |
| `review_count` | 별점 수 | 읽기 전용 |
| `last_visited_on` | 가장 최근 방문일(한국 날짜). 방문이 없으면 `null` | 읽기 전용 |

### GET /groups/{group_id}/restaurants (F06)
그룹의 삭제되지 않은 식당 목록이다. 이름 오름차순으로 정렬한다.

쿼리 (둘 다 선택, 함께 주면 AND)
| 이름 | 설명 |
|---|---|
| `q` | 이름에 이 글자가 포함된 식당 (공백 제거 후 비어 있으면 무시) |
| `category` | 이 카테고리의 식당 |

예: `GET /groups/{group_id}/restaurants?q=순대&category=KOREAN`

응답 `200`
```json
{ "items": [ { "id": 12, "name": "할머니 순대국", "...": "식당 객체" } ] }
```

오류: `422` 잘못된 `category`

### POST /groups/{group_id}/restaurants (F03, F04)
요청
```json
{
  "name": "할머니 순대국",
  "category": "KOREAN",
  "price_level": 1,
  "walk_minutes": 7,
  "map_url": null,
  "memo": ""
}
```
`name`, `category`만 필수이고 나머지는 생략하면 기본값을 쓴다.

응답 `201`: 식당 객체

오류: `422` 빈 이름, 잘못된 카테고리, 범위를 벗어난 가격대·도보 시간, 잘못된 URL, 메모 200자 초과

### GET /groups/{group_id}/restaurants/{id} (F13)
식당 객체에 방문 이력과 한 줄 평을 더해 돌려준다.

응답 `200`
```json
{
  "id": 12,
  "name": "할머니 순대국",
  "...": "식당 객체의 나머지 필드",
  "visits": [
    {
      "id": 31,
      "visited_on": "2026-10-10",
      "reviews": [
        { "id": 88, "member": { "id": 2, "nickname": "준호" }, "rating": 5, "comment": "국물 진함", "created_at": "2026-10-10T05:10:00Z" }
      ]
    }
  ]
}
```
- `visits`는 최근 방문부터 정렬한다.

오류: `404 RESTAURANT_NOT_FOUND` (없음, 다른 그룹, 삭제됨)

### PATCH /groups/{group_id}/restaurants/{id} (F03, F04)
보낸 필드만 바꾸고 보내지 않은 필드는 그대로 둔다.

요청 (예: 도보 시간만 지우고 메모만 수정)
```json
{ "walk_minutes": null, "memo": "주말 휴무" }
```
- `walk_minutes`, `map_url`은 `null`을 보내면 값이 지워진다.
- `name`, `category`, `price_level`, `memo`에 `null`을 보내면 `422`이다.

응답 `200`: 수정된 식당 객체

오류: `404 RESTAURANT_NOT_FOUND`, `422` 등록과 같은 규칙 위반

### DELETE /groups/{group_id}/restaurants/{id} (F05)
`deleted_at`을 기록하는 소프트 삭제다. 삭제한 식당은 목록과 뽑기에서 빠지지만 방문 기록과 별점은 남는다. 삭제 전 확인은 화면에서 한다.

응답 `204` (본문 없음)

오류: `404 RESTAURANT_NOT_FOUND` (이미 삭제된 식당 포함)

---

## 카드 뽑기와 투표

### 뽑기 객체
`POST /groups/{group_id}/draws`, `GET /groups/{group_id}/draws/current`, `GET /groups/{group_id}/draws/{id}`, 다시 뽑기, 투표, 마감 응답에 공통으로 쓴다.

```json
{
  "id": 5,
  "status": "OPEN",
  "created_by": { "id": 1, "nickname": "민지" },
  "filters": { "exclude_categories": ["CHINESE"], "max_price_level": 2, "max_walk_minutes": 10 },
  "round": 1,
  "redraw_used": false,
  "candidates": [
    { "restaurant_id": 12, "name": "할머니 순대국", "category": "KOREAN", "price_level": 1, "walk_minutes": 7, "avg_rating": 4.3, "vote_count": 2 },
    { "restaurant_id": 15, "name": "스시 한판", "category": "JAPANESE", "price_level": 2, "walk_minutes": 9, "avg_rating": null, "vote_count": 1 }
  ],
  "my_vote_restaurant_id": 12,
  "decided_restaurant_id": null,
  "visit_id": null,
  "created_at": "2026-10-14T02:50:00Z",
  "closed_at": null
}
```
- `status`: `OPEN`(진행 중) 또는 `CLOSED`(마감).
- `candidates`: 현재 라운드의 후보만 담는다. 처음 뽑으면 `round`가 1, 다시 뽑으면 2다.
- `my_vote_restaurant_id`: 요청한 멤버의 현재 표. 투표하지 않았으면 `null`.
- 마감 후에는 `decided_restaurant_id`와 `visit_id`가 채워진다.
- 카드 뒤집기는 화면에서만 처리한다. 서버는 후보를 처음부터 모두 돌려준다.

### POST /groups/{group_id}/draws (F07, F08)
조건에 맞는 식당 중 최대 3곳을 서버가 무작위로 뽑는다. 그룹마다 진행 중인 뽑기는 1개뿐이다.

요청
```json
{ "exclude_categories": ["CHINESE"], "max_price_level": 2, "max_walk_minutes": 10 }
```

| 필드 | 규칙 | 생략 또는 `null`일 때 |
|---|---|---|
| `exclude_categories` | 카테고리 목록, 중복 허용 안 함 | 제외 없음 (`[]`) |
| `max_price_level` | 1~3 | 가격 조건 없음 |
| `max_walk_minutes` | 0~60 정수. 지정하면 도보 시간이 `null`인 식당은 제외 | 거리 조건 없음 |

- 조건은 모두 AND로 적용하고, 삭제된 식당은 항상 제외한다.
- 맞는 식당이 1~2곳이면 그만큼만 후보가 된다.

응답 `201`: 뽑기 객체

오류
- `409 ACTIVE_DRAW_EXISTS`: 그룹에 `OPEN` 상태인 뽑기가 이미 있음
- `422 NO_CANDIDATES`: 조건에 맞는 식당이 0곳 (화면은 조건을 완화하라고 안내한다)
- `422`: 잘못된 카테고리, 범위를 벗어난 값

### GET /groups/{group_id}/draws/current (F08, F10)
그룹에서 진행 중인(`OPEN`) 뽑기다. 홈 화면은 이 API로 참여할 뽑기가 있는지 확인한다.

응답 `200`
```json
{ "draw": { "id": 5, "...": "뽑기 객체" } }
```
진행 중인 뽑기가 없으면 `{ "draw": null }`이다. 3초 폴링 중에 콘솔에 404가 쌓이지 않도록 404 대신 `null`을 쓴다.

### GET /groups/{group_id}/draws/{id} (F08, F10, F11)
특정 뽑기의 현재 상태다. 투표 화면은 이 API를 3초마다 호출해 득표와 마감 여부를 갱신한다.

응답 `200`: 뽑기 객체

오류: `404 DRAW_NOT_FOUND` (없음 또는 다른 그룹)

### POST /groups/{group_id}/draws/{id}/redraw (F09)
뽑기를 만든 멤버만 세션당 1회 할 수 있다. 처음 조건 그대로 뽑되 직전 라운드 후보는 제외하고, 기존 투표는 모두 지운다.

요청 본문 없음

응답 `200`: `round`가 2이고 `redraw_used`가 `true`인 뽑기 객체

오류
- `403 NOT_DRAW_CREATOR`
- `404 DRAW_NOT_FOUND`
- `409 REDRAW_ALREADY_USED`
- `409 DRAW_CLOSED`
- `422 NO_CANDIDATES`: 직전 후보를 빼면 남는 식당이 없음. 이때 기존 후보와 투표는 그대로 유지하고 `redraw_used`도 바꾸지 않는다.

### PUT /groups/{group_id}/draws/{id}/vote (F10)
현재 후보 중 한 곳에 1표를 던진다. 다시 호출하면 표가 옮겨지고 표 수는 늘지 않는다.

요청
```json
{ "restaurant_id": 15 }
```

응답 `200`: 뽑기 객체

오류
- `404 DRAW_NOT_FOUND`
- `409 DRAW_CLOSED`: 마감 후 투표
- `422 NOT_A_CANDIDATE`: 현재 라운드 후보가 아닌 식당

### POST /groups/{group_id}/draws/{id}/close (F11)
뽑기를 만든 멤버만 마감할 수 있다. 서버가 결과를 정한다.

1. 표가 있으면 최다 득표 식당을 고른다. 동점이면 동점 후보 중에서 무작위로 고른다.
2. 표가 하나도 없으면 전체 후보 중에서 무작위로 고른다.
3. 결정한 식당으로 방문 기록 1건을 만든다. `visited_on`은 마감 시각의 한국 날짜다.

요청 본문 없음

응답 `200`: `status`가 `CLOSED`이고 `decided_restaurant_id`, `visit_id`, `closed_at`이 채워진 뽑기 객체

- 이미 마감된 뽑기를 다시 마감하면 결과를 바꾸지 않고 같은 뽑기 객체를 `200`으로 돌려준다. 방문 기록도 새로 만들지 않는다.

오류
- `403 NOT_DRAW_CREATOR` (이미 마감된 경우에도 생성자가 아니면 403)
- `404 DRAW_NOT_FOUND`

---

## 방문과 별점

### GET /groups/{group_id}/visits/pending-review (F12)
그룹의 방문 기록 중 내가 아직 별점을 남기지 않은 것이다. 최근 방문부터 정렬한다. 내가 그룹에 들어오기 전에 마감된 뽑기의 방문은 포함하지 않는다.

응답 `200`
```json
{
  "items": [
    { "visit_id": 31, "visited_on": "2026-10-14", "restaurant": { "id": 12, "name": "할머니 순대국", "deleted": false } }
  ]
}
```
- 식당이 삭제되어도 방문 기록은 남기 때문에 `deleted: true`로 표시한다.

### POST /groups/{group_id}/visits/{id}/reviews (F12)
방문 기록 하나에 멤버당 별점 1회를 남긴다.

요청
```json
{ "rating": 5, "comment": "국물 진함" }
```

| 필드 | 규칙 | 기본값 |
|---|---|---|
| `rating` | 필수, 1~5 정수 | - |
| `comment` | 공백 제거 후 최대 100자 | `""` |

응답 `201`
```json
{ "id": 88, "visit_id": 31, "member": { "id": 2, "nickname": "준호" }, "rating": 5, "comment": "국물 진함", "created_at": "2026-10-14T05:10:00Z" }
```

오류
- `404 VISIT_NOT_FOUND` (없음 또는 다른 그룹)
- `409 ALREADY_REVIEWED`: 같은 방문에 두 번째 별점
- `422`: 별점 0 또는 6, 정수가 아닌 별점, 101자 이상 한 줄 평

---

## PRD 요구사항 대응표

| PRD | 내용 | API |
|---|---|---|
| F01 | 그룹 생성, 6자리 초대 코드 | `POST /groups` |
| F02 | 초대 코드 참여, 내 그룹 목록, 그룹 선택 | `POST /groups/join`, `GET /groups`, `GET /groups/{group_id}` |
| F03 | 식당 등록·수정, 이름·카테고리 필수 | `POST /groups/{group_id}/restaurants`, `PATCH /groups/{group_id}/restaurants/{id}` |
| F04 | 가격대·도보 시간·지도 링크·메모 규칙 | `POST /groups/{group_id}/restaurants`, `PATCH /groups/{group_id}/restaurants/{id}` |
| F05 | 식당 삭제, 기록은 유지 | `DELETE /groups/{group_id}/restaurants/{id}` |
| F06 | 이름 검색·카테고리 필터, 평균 별점·최근 방문일 | `GET /groups/{group_id}/restaurants` |
| F07 | 뽑기 조건 (제외 카테고리, 최대 가격대, 최대 도보 시간) | `POST /groups/{group_id}/draws` |
| F08 | 최대 3곳 무작위, 0곳 거절, 진행 중 1개 | `POST /groups/{group_id}/draws`, `GET /groups/{group_id}/draws/current`, `GET /groups/{group_id}/draws/{id}` |
| F09 | 생성자 1회 다시 뽑기, 직전 후보 제외, 투표 초기화 | `POST /groups/{group_id}/draws/{id}/redraw` |
| F10 | 1인 1표, 마감 전 변경, 3초 갱신 | `PUT /groups/{group_id}/draws/{id}/vote`, `GET /groups/{group_id}/draws/{id}` |
| F11 | 생성자만 마감, 최다 득표·동점·무투표 처리, 방문 기록 | `POST /groups/{group_id}/draws/{id}/close` |
| F12 | 방문당 멤버별 별점 1회와 한 줄 평 | `GET /groups/{group_id}/visits/pending-review`, `POST /groups/{group_id}/visits/{id}/reviews` |
| F13 | 식당 상세: 평균 별점, 방문 이력, 한 줄 평 | `GET /groups/{group_id}/restaurants/{id}` |
| F14 | 회원가입, 아이디·닉네임 중복 불가 | `POST /auth/signup` |
| F15 | 로그인·로그아웃, 세션 토큰 30일 | `POST /auth/login`, `POST /auth/logout`, `GET /me` |

## PRD에 없어 이 문서에서 정한 것
구현 전에 바꾸려면 이 목록을 먼저 고친다.

1. 닉네임은 계정에 하나이며 전체 서비스에서 중복될 수 없다. 그래서 어느 그룹에 참여해도 그룹 안에서 닉네임이 겹치지 않는다(PRD F02의 그룹 안 중복 불가를 자동으로 만족).
2. 토큰은 `Authorization: Bearer` 헤더로 보낸다.
3. 내가 멤버가 아닌 그룹과 그 데이터에 접근하면 403이 아니라 404로 응답한다.
4. `map_url`은 `http`/`https`만 허용하고 최대 500자다. `javascript:` 링크 실행을 막기 위해서다.
5. 초대 코드는 대소문자를 구분하지 않는다.
6. 이미 마감된 뽑기의 마감 요청은 오류 대신 같은 결과를 돌려준다(PLAN T17 "두 번 호출해도 visits는 1건").
7. 다시 뽑기에서 남는 식당이 없으면 `422 NO_CANDIDATES`로 거절하고 다시 뽑기 횟수를 쓰지 않은 것으로 둔다.
8. 평가 대기 목록에는 내가 그룹에 참여하기 전에 마감된 뽑기의 방문을 넣지 않는다.
9. 평균 별점은 소수 둘째 자리에서 반올림(half-up)한다. SQL `ROUND(AVG(rating), 1)`과 같은 값이다.
10. 아이디는 소문자로 바꿔 저장하므로 대소문자를 구분하지 않는다.
11. 회원가입하면 바로 로그인 상태가 된다(토큰 발급).
12. 로그인할 때마다 새 세션을 만들어 여러 기기에서 동시에 로그인할 수 있고, 로그아웃은 현재 기기의 세션만 끝낸다.
13. 그룹 안의 데이터는 `/groups/{group_id}/...` 경로로 구분한다. 헤더로 그룹을 고르는 방식보다 요청만 보고 어느 그룹인지 알 수 있다.
