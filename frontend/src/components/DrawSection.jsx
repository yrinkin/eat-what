import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import DrawCard from './DrawCard'
import DrawForm from './DrawForm'

// F07, F08: 진행 중인 뽑기가 없으면 조건 폼, 있으면 뒤집힌 카드를 보여 준다.
function DrawSection({ groupId }) {
  const [draw, setDraw] = useState(undefined) // undefined: 불러오는 중, null: 진행 중인 뽑기 없음
  const [error, setError] = useState('')
  // 카드 공개 상태는 이 화면에만 해당한다. 뽑기·라운드가 바뀌면 다시 덮는다.
  const [revealed, setRevealed] = useState({ key: null, ids: [] })
  const [voteNotice, setVoteNotice] = useState('')

  const load = useCallback(() => {
    return api(`/groups/${groupId}/draws/current`)
      .then((data) => {
        setError('')
        setDraw(data.draw)
      })
      .catch((err) => setError(err.message))
  }, [groupId])

  useEffect(() => {
    load()
  }, [load])

  if (error) return <p className="error">{error}</p>
  if (draw === undefined) return <p>불러오는 중...</p>

  if (draw === null) {
    return (
      <section className="draw-section">
        <h3>오늘의 뽑기</h3>
        <DrawForm groupId={groupId} onDrawn={setDraw} onConflict={load} />
      </section>
    )
  }

  const drawKey = `${draw.id}:${draw.round}`
  const revealedIds = revealed.key === drawKey ? revealed.ids : []
  const allRevealed = draw.candidates.every((c) => revealedIds.includes(c.restaurant_id))

  function reveal(restaurantId) {
    setRevealed({ key: drawKey, ids: [...revealedIds, restaurantId] })
  }

  return (
    <section className="draw-section">
      <h3>오늘의 뽑기</h3>
      <p className="hint">
        {draw.created_by.nickname}님이 뽑은 후보 {draw.candidates.length}곳 · {revealedIds.length}장 공개
      </p>
      <div className="draw-cards">
        {draw.candidates.map((candidate, index) => (
          <DrawCard
            key={candidate.restaurant_id}
            candidate={candidate}
            index={index}
            revealed={revealedIds.includes(candidate.restaurant_id)}
            onReveal={() => reveal(candidate.restaurant_id)}
          />
        ))}
      </div>
      <button
        type="button"
        className="primary vote-button"
        disabled={!allRevealed}
        onClick={() => setVoteNotice('투표 기능은 다음 단계에서 열려요.')}
      >
        {allRevealed ? '투표하기' : '카드를 모두 공개하면 투표할 수 있어요'}
      </button>
      {voteNotice && <p className="hint">{voteNotice}</p>}
    </section>
  )
}

export default DrawSection
