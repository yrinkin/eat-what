import { useEffect, useState } from 'react'
import { api } from '../api'

// 그룹 첫 화면. 식당 목록, 뽑기 등은 이후 작업에서 추가한다.
function GroupPage({ groupId, onBack }) {
  const [group, setGroup] = useState(null)
  const [error, setError] = useState(null)

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

  return (
    <section className="group">
      <button type="button" className="link-button" onClick={onBack}>
        ← 내 그룹 목록
      </button>
      <h2>{group.name}</h2>
      <dl className="group-info">
        <dt>초대 코드</dt>
        <dd className="code">{group.invite_code}</dd>
        <dt>멤버</dt>
        <dd>
          <ul className="member-list">
            {group.members.map((member) => (
              <li key={member.id}>
                {member.nickname}
                {member.id === group.my_member_id && ' (나)'}
              </li>
            ))}
          </ul>
        </dd>
      </dl>
      <p className="hint">팀원에게 초대 코드를 알려 주면 같은 그룹에 참여할 수 있어요.</p>
    </section>
  )
}

export default GroupPage
