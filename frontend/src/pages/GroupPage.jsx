import { useEffect, useState } from 'react'
import { api } from '../api'
import DrawSection from '../components/DrawSection'
import PendingReviews from '../components/PendingReviews'
import RestaurantDetail from '../components/RestaurantDetail'
import RestaurantList from '../components/RestaurantList'

// 그룹 첫 화면(홈): 평가 대기, 오늘의 뽑기, 식당 목록. 식당 이름을 누르면 상세(F13).
function GroupPage({ groupId, onBack }) {
  const [group, setGroup] = useState(null)
  const [error, setError] = useState(null)
  // 뽑기가 마감돼 새 방문 기록이 생기면 평가 대기 목록을 다시 불러온다.
  const [visitsVersion, setVisitsVersion] = useState(0)
  // 식당 상세를 열면 그룹 홈 대신 상세를 보여 준다.
  const [openRestaurantId, setOpenRestaurantId] = useState(null)

  useEffect(() => {
    api(`/groups/${groupId}`)
      .then(setGroup)
      .catch((err) => {
        // 없는 그룹이거나 멤버가 아니면 목록으로 돌아간다.
        if (err.status === 404) onBack()
        else setError(err)
      })
  }, [groupId, onBack])

  if (error) return <p className="error">{error.message}</p>
  if (!group) return <p>불러오는 중...</p>

  if (openRestaurantId !== null) {
    return (
      <RestaurantDetail
        groupId={groupId}
        restaurantId={openRestaurantId}
        onBack={() => setOpenRestaurantId(null)}
      />
    )
  }

  return (
    <section className="group">
      {/* 좁은 화면에서만 보인다. 넓은 화면에서는 왼쪽에 그룹 목록이 늘 있다. */}
      <button type="button" className="link-button narrow-only" onClick={onBack}>
        ← 내 그룹 목록
      </button>
      <h2>{group.name}</h2>
      <dl className="group-info">
        <dt>초대 코드</dt>
        <dd className="code">{group.invite_code}</dd>
        <dt>멤버</dt>
        <dd>
          <ul className="member-chips">
            {group.members.map((member) => {
              const me = member.id === group.my_member_id
              return (
                <li key={member.id} className={me ? 'member-chip me' : 'member-chip'}>
                  {member.nickname}
                  {me && <span className="visually-hidden"> (나)</span>}
                </li>
              )
            })}
          </ul>
        </dd>
      </dl>
      <p className="hint">팀원에게 초대 코드를 알려 주면 같은 그룹에 참여할 수 있어요.</p>
      <PendingReviews groupId={groupId} reloadKey={visitsVersion} />
      <DrawSection
        groupId={groupId}
        myMemberId={group.my_member_id}
        onDecided={() => setVisitsVersion((n) => n + 1)}
      />
      <RestaurantList groupId={groupId} onOpen={setOpenRestaurantId} />
    </section>
  )
}

export default GroupPage
