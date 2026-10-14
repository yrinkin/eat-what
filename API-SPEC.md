# 오늘 뭐 먹지? API 명세

PRD.md의 F01~F13을 구현하는 HTTP API 계약이다. 구현 순서는 PLAN.md를 따르고, 이 문서와 구현이 다르면 구현 전에 이 문서를 먼저 고친다.

## 공통 규칙

### 주소
- 모든 경로 앞에 `/api/v1`이 붙는다. 아래 표와 예시는 이를 생략한다.
- 요청·응답 본문은 JSON(UTF-8)이다.

### 인증
- 그룹 생성·입장 응답의 `token`을 브라우저 localStorage(`lunch-token-v1`)에 저장한다.
- 인증이 필요한 요청은 헤더에 토큰을 보낸다.
  ```
  Authorization: Bearer <token>
  ```
- 인증 없이 호출하는 API: `GET /health`, `POST /groups`, `POST /groups/join`. 나머지는 모두 토큰이 필요하다.
- 서버는 토큰으로 멤버와 그룹을 찾고, 모든 조회·변경을 그 그룹 안으로 제한한다.

### 식별자와 시각
- 수정, 삭제, 투표, 별점은 화면 순번이 아니라 고유 `id`로 요청한다.
- 시각(`*_at`)은 UTC ISO 8601 문자열이다. 예: `"2026-10-14T03:20:00Z"`. 화면에서 한국 시간으로 바꿔 표시한다.
- 날짜(`visited_on`)는 한국 시간 기준 `"YYYY-MM-DD"`이다.

### 입력 정리
- 그룹명, 닉네임, 식당 이름, 한 줄 평은 앞뒤 공백을 제거한 뒤 길이를 검사한다.
- 초대 코드는 앞뒤 공백을 제거하고 대문자로 바꾼 뒤 비교한다.
- 서버는 사용자 입력을 그대로 저장하고 그대로 돌려준다. 화면은 이를 HTML로 실행하지 않고 글자로 표시한다.

### 오류 응답

| 코드 | 의미 | 대표 상황 |
|---|---|---|
| 401 | 인증 실패 | 토큰이 없거나 맞지 않음 |
| 403 | 권한 없음 | 뽑기를 만들지 않은 멤버가 마감·다시 뽑기 요청 |
| 404 | 찾을 수 없음 | 없는 초대 코드, 없는 id, **다른 그룹의 데이터**, 삭제된 식당 |
| 409 | 현재 상태와 충돌 | 중복 닉네임, 진행 중인 뽑기 있음, 마감 후 투표, 다시 뽑기 2회째, 같은 방문에 두 번째 별점 |
| 422 | 입력값 오류 | 길이·범위·형식 위반, 조건에 맞는 식당 0곳, 후보가 아닌 식당에 투표 |

다른 그룹의 데이터는 403이 아니라 404로 응답해 존재 여부를 알려 주지 않는다.

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
| `UNAUTHORIZED` | 401 | 토큰 없음 또는 잘못된 토큰 |
| `NOT_DRAW_CREATOR` | 403 | 뽑기를 만든 멤버만 할 수 있는 요청 |
| `GROUP_NOT_FOUND` | 404 | 초대 코드에 해당하는 그룹 없음 |
| `RESTAURANT_NOT_FOUND` | 404 | 식당 없음, 다른 그룹, 삭제됨 |
| `DRAW_NOT_FOUND` | 404 | 뽑기 없음 또는 다른 그룹 |
| `VISIT_NOT_FOUND` | 404 | 방문 기록 없음 또는 다른 그룹 |
| `DUPLICATE_NICKNAME` | 409 | 그룹 안에 같은 닉네임 있음 |
| `ACTIVE_DRAW_EXISTS` | 409 | 그룹에 진행 중인 뽑기가 이미 있음 |
| `DRAW_CLOSED` | 409 | 마감된 뽑기에 투표·다시 뽑기 |
| `REDRAW_ALREADY_USED` | 409 | 다시 뽑기를 이미 사용함 |
| `ALREADY_REVIEWED` | 409 | 같은 방문에 이미 별점을 남김 |
| `NO_CANDIDATES` | 422 | 조건에 맞는 식당이 0곳 |
| `NOT_A_CANDIDATE` | 422 | 현재 후보가 아닌 식당에 투표 |

## 엔드포인트 목록

| 메서드 | 경로 | 인증 | 설명 | PRD | PLAN |
|---|---|---|---|---|---|
| GET | `/health` | - | 서버와 DB 상태 | - | T02 |
| POST | `/groups` | - | 그룹 생성 + 생성자 입장 | F01 | T07 |
| POST | `/groups/join` | - | 초대 코드로 입장 | F02 | T07 |
| GET | `/me` | ✓ | 내 멤버·그룹 정보 | F02 | T07 |
| GET | `/restaurants` | ✓ | 식당 목록, 검색·필터 | F06 | T09, T11 |
| POST | `/restaurants` | ✓ | 식당 등록 | F03, F04 | T09 |
| GET | `/restaurants/{id}` | ✓ | 식당 상세 (평균 별점, 방문 이력, 한 줄 평) | F13 | T09, T21 |
| PATCH | `/restaurants/{id}` | ✓ | 식당 수정 (보낸 필드만) | F03, F04 | T09 |
| DELETE | `/restaurants/{id}` | ✓ | 식당 삭제 (소프트 삭제) | F05 | T09 |
| POST | `/draws` | ✓ | 카드 뽑기 시작 | F07, F08 | T14 |
| GET | `/draws/current` | ✓ | 진행 중인 뽑기 | F08, F10 | T14 |
| GET | `/draws/{id}` | ✓ | 뽑기 상세 (후보, 득표, 결과) | F08, F10, F11 | T14 |
| POST | `/draws/{id}/redraw` | ✓ | 다시 뽑기 | F09 | T22 |
| PUT | `/draws/{id}/vote` | ✓ | 투표 또는 표 변경 | F10 | T16 |
| POST | `/draws/{id}/close` | ✓ | 마감과 결정 | F11 | T17 |
| GET | `/visits/pending-review` | ✓ | 내가 아직 평가하지 않은 방문 | F12 | T19 |
| POST | `/visits/{id}/reviews` | ✓ | 별점과 한 줄 평 등록 | F12 | T19 |

---

## 상태 확인

### GET /health
DB에 `SELECT 1`을 실행해 상태를 돌려준다.

- `200` `{ "status": "ok", "db": "ok" }`
- `503` `{ "status": "error", "db": "error" }`

---

## 그룹과 멤버

### POST /groups (F01)
그룹을 만들고, 만든 사람을 첫 멤버로 등록한다.

요청
```json
{ "group_name": "개발팀 점심", "nickname": "민지" }
```

| 필드 | 규칙 |
|---|---|
| `group_name` | 필수, 공백 제거 후 1~30자 |
| `nickname` | 필수, 공백 제거 후 1~20자 |

응답 `201`
```json
{
  "token": "q9X2...(서버가 만든 무작위 문자열)",
  "member": { "id": 1, "nickname": "민지" },
  "group": { "id": 1, "name": "개발팀 점심", "invite_code": "K7Q2MZ" }
}
```
- `invite_code`는 영문 대문자와 숫자로 된 6자리이며 그룹마다 다르다. 겹치면 서버가 다시 만든다.

오류: `422` 빈 그룹명, 빈 닉네임, 길이 초과

### POST /groups/join (F02)
초대 코드와 닉네임으로 그룹에 들어간다.

요청
```json
{ "invite_code": "k7q2mz", "nickname": "준호" }
```

| 필드 | 규칙 |
|---|---|
| `invite_code` | 필수, 공백 제거·대문자 변환 후 비교 |
| `nickname` | 필수, 공백 제거 후 1~20자, 그룹 안에서 중복 불가 |

응답 `201`: `POST /groups`와 같은 형식이다.

오류
- `404 GROUP_NOT_FOUND`: 없는 초대 코드
- `409 DUPLICATE_NICKNAME`: 같은 그룹에 같은 닉네임이 있음
- `422`: 빈 닉네임, 길이 초과

### GET /me (F02)
저장된 토큰이 유효한지 확인하고 내 정보를 돌려준다. 화면은 새로고침할 때 이 API로 입장 상태를 복원한다.

응답 `200`
```json
{
  "member": { "id": 2, "nickname": "준호" },
  "group": { "id": 1, "name": "개발팀 점심", "invite_code": "K7Q2MZ" }
}
```

오류: `401 UNAUTHORIZED` (화면은 저장된 토큰을 지우고 입장 화면으로 이동한다)

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

### GET /restaurants (F06)
내 그룹의 삭제되지 않은 식당 목록이다. 이름 오름차순으로 정렬한다.

쿼리 (둘 다 선택, 함께 주면 AND)
| 이름 | 설명 |
|---|---|
| `q` | 이름에 이 글자가 포함된 식당 (공백 제거 후 비어 있으면 무시) |
| `category` | 이 카테고리의 식당 |

예: `GET /restaurants?q=순대&category=KOREAN`

응답 `200`
```json
{ "items": [ { "id": 12, "name": "할머니 순대국", "...": "식당 객체" } ] }
```

오류: `422` 잘못된 `category`

### POST /restaurants (F03, F04)
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

### GET /restaurants/{id} (F13)
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

### PATCH /restaurants/{id} (F03, F04)
보낸 필드만 바꾸고 보내지 않은 필드는 그대로 둔다.

요청 (예: 도보 시간만 지우고 메모만 수정)
```json
{ "walk_minutes": null, "memo": "주말 휴무" }
```
- `walk_minutes`, `map_url`은 `null`을 보내면 값이 지워진다.
- `name`, `category`, `price_level`, `memo`에 `null`을 보내면 `422`이다.

응답 `200`: 수정된 식당 객체

오류: `404 RESTAURANT_NOT_FOUND`, `422` 등록과 같은 규칙 위반

### DELETE /restaurants/{id} (F05)
`deleted_at`을 기록하는 소프트 삭제다. 삭제한 식당은 목록과 뽑기에서 빠지지만 방문 기록과 별점은 남는다. 삭제 전 확인은 화면에서 한다.

응답 `204` (본문 없음)

오류: `404 RESTAURANT_NOT_FOUND` (이미 삭제된 식당 포함)

---

## 카드 뽑기와 투표

### 뽑기 객체
`POST /draws`, `GET /draws/current`, `GET /draws/{id}`, 다시 뽑기, 투표, 마감 응답에 공통으로 쓴다.

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

### POST /draws (F07, F08)
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

### GET /draws/current (F08, F10)
그룹에서 진행 중인(`OPEN`) 뽑기다. 홈 화면은 이 API로 참여할 뽑기가 있는지 확인한다.

응답 `200`
```json
{ "draw": { "id": 5, "...": "뽑기 객체" } }
```
진행 중인 뽑기가 없으면 `{ "draw": null }`이다. 3초 폴링 중에 콘솔에 404가 쌓이지 않도록 404 대신 `null`을 쓴다.

### GET /draws/{id} (F08, F10, F11)
특정 뽑기의 현재 상태다. 투표 화면은 이 API를 3초마다 호출해 득표와 마감 여부를 갱신한다.

응답 `200`: 뽑기 객체

오류: `404 DRAW_NOT_FOUND` (없음 또는 다른 그룹)

### POST /draws/{id}/redraw (F09)
뽑기를 만든 멤버만 세션당 1회 할 수 있다. 처음 조건 그대로 뽑되 직전 라운드 후보는 제외하고, 기존 투표는 모두 지운다.

요청 본문 없음

응답 `200`: `round`가 2이고 `redraw_used`가 `true`인 뽑기 객체

오류
- `403 NOT_DRAW_CREATOR`
- `404 DRAW_NOT_FOUND`
- `409 REDRAW_ALREADY_USED`
- `409 DRAW_CLOSED`
- `422 NO_CANDIDATES`: 직전 후보를 빼면 남는 식당이 없음. 이때 기존 후보와 투표는 그대로 유지하고 `redraw_used`도 바꾸지 않는다.

### PUT /draws/{id}/vote (F10)
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

### POST /draws/{id}/close (F11)
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

### GET /visits/pending-review (F12)
내 그룹의 방문 기록 중 내가 아직 별점을 남기지 않은 것이다. 최근 방문부터 정렬한다. 내가 그룹에 들어오기 전에 마감된 뽑기의 방문은 포함하지 않는다.

응답 `200`
```json
{
  "items": [
    { "visit_id": 31, "visited_on": "2026-10-14", "restaurant": { "id": 12, "name": "할머니 순대국", "deleted": false } }
  ]
}
```
- 식당이 삭제되어도 방문 기록은 남기 때문에 `deleted: true`로 표시한다.

### POST /visits/{id}/reviews (F12)
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
| F02 | 초대 코드 입장, 닉네임 중복 불가, 토큰 저장 | `POST /groups/join`, `GET /me` |
| F03 | 식당 등록·수정, 이름·카테고리 필수 | `POST /restaurants`, `PATCH /restaurants/{id}` |
| F04 | 가격대·도보 시간·지도 링크·메모 규칙 | `POST /restaurants`, `PATCH /restaurants/{id}` |
| F05 | 식당 삭제, 기록은 유지 | `DELETE /restaurants/{id}` |
| F06 | 이름 검색·카테고리 필터, 평균 별점·최근 방문일 | `GET /restaurants` |
| F07 | 뽑기 조건 (제외 카테고리, 최대 가격대, 최대 도보 시간) | `POST /draws` |
| F08 | 최대 3곳 무작위, 0곳 거절, 진행 중 1개 | `POST /draws`, `GET /draws/current`, `GET /draws/{id}` |
| F09 | 생성자 1회 다시 뽑기, 직전 후보 제외, 투표 초기화 | `POST /draws/{id}/redraw` |
| F10 | 1인 1표, 마감 전 변경, 3초 갱신 | `PUT /draws/{id}/vote`, `GET /draws/{id}` |
| F11 | 생성자만 마감, 최다 득표·동점·무투표 처리, 방문 기록 | `POST /draws/{id}/close` |
| F12 | 방문당 멤버별 별점 1회와 한 줄 평 | `GET /visits/pending-review`, `POST /visits/{id}/reviews` |
| F13 | 식당 상세: 평균 별점, 방문 이력, 한 줄 평 | `GET /restaurants/{id}` |

## PRD에 없어 이 문서에서 정한 것
구현 전에 바꾸려면 이 목록을 먼저 고친다.

1. 닉네임 길이는 그룹 생성(F01)과 입장(F02) 모두 1~20자로 통일했다. F01 문장은 "1~30자의 그룹명과 닉네임"으로 읽힐 수 있지만 F02는 닉네임을 1~20자로 정한다.
2. 토큰은 `Authorization: Bearer` 헤더로 보낸다.
3. 다른 그룹의 데이터 접근은 403이 아니라 404로 응답한다.
4. `map_url`은 `http`/`https`만 허용하고 최대 500자다. `javascript:` 링크 실행을 막기 위해서다.
5. 초대 코드는 대소문자를 구분하지 않는다.
6. 이미 마감된 뽑기의 마감 요청은 오류 대신 같은 결과를 돌려준다(PLAN T17 "두 번 호출해도 visits는 1건").
7. 다시 뽑기에서 남는 식당이 없으면 `422 NO_CANDIDATES`로 거절하고 다시 뽑기 횟수를 쓰지 않은 것으로 둔다.
8. 평가 대기 목록에는 내가 입장하기 전에 마감된 뽑기의 방문을 넣지 않는다.
9. 평균 별점은 소수 둘째 자리에서 반올림(half-up)한다. SQL `ROUND(AVG(rating), 1)`과 같은 값이다.
