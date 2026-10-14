import { useCallback, useRef, useState } from 'react'
import { api } from '../api'
import usePolling from '../hooks/usePolling'
import { CATEGORY_LABELS, decisionNote } from '../labels'
import DrawCard from './DrawCard'
import DrawForm from './DrawForm'

const POLL_MS = 3000

function formatKst(utcIso) {
  return new Date(utcIso).toLocaleString('ko-KR', {
    timeZone: 'Asia/Seoul',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// F07~F11: 조건 폼 → 뒤집힌 카드와 투표(3초 갱신, 생성자는 1회 다시 뽑기 F09) → 마감 결과.
function DrawSection({ groupId, myMemberId, onDecided }) {
  const [draw, setDraw] = useState(undefined) // undefined: 불러오는 중, null: 진행 중인 뽑기 없음
  const [loadError, setLoadError] = useState('')
  const [actionError, setActionError] = useState('')
  const [busy, setBusy] = useState(false)
  // 카드 공개 상태는 이 화면에만 해당한다. 뽑기·라운드가 바뀌면 다시 덮는다.
  const [revealed, setRevealed] = useState({ key: null, ids: [] })

  // 요청 순서 번호. 더 늦게 보낸 요청의 결과가 이미 반영됐으면 오래된 응답은 버린다.
  const seq = useRef({ next: 0, applied: -1 })
  const request = useCallback(async (path, options) => {
    const mine = seq.current.next++
    const data = await api(path, options)
    const fresh = mine > seq.current.applied
    if (fresh) seq.current.applied = mine
    return { data, fresh }
  }, [])

  const isOpen = draw?.status === 'OPEN'
  const pollPath = draw === undefined || draw === null ? `/groups/${groupId}/draws/current` : isOpen ? `/groups/${groupId}/draws/${draw.id}` : null

  usePolling(
    async () => {
      try {
        const { data, fresh } = await request(pollPath)
        if (!fresh) return
        setLoadError('')
        const next = pollPath.endsWith('/current') ? data.draw : data
        // 다른 멤버가 마감한 것을 갱신으로 알게 된 경우
        if (next?.status === 'CLOSED') onDecided?.()
        setDraw(next)
      } catch (err) {
        setLoadError(err.message)
      }
    },
    POLL_MS,
    { enabled: pollPath !== null, key: pollPath },
  )

  async function mutate(path, options) {
    setActionError('')
    setBusy(true)
    try {
      const { data, fresh } = await request(path, options)
      if (data?.status === 'CLOSED') onDecided?.()
      if (fresh) setDraw(data)
    } catch (err) {
      setActionError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function handleDrawn(created) {
    seq.current.applied = seq.current.next++
    setDraw(created)
  }

  function handleConflict() {
    // 다른 멤버가 먼저 뽑았다: current를 다시 불러오도록 한다.
    setDraw(undefined)
  }

  if (draw === undefined) {
    return (
      <section className="draw-section">
        <h3>오늘의 뽑기</h3>
        {loadError ? <p className="error">{loadError}</p> : <p className="loading">불러오는 중...</p>}
      </section>
    )
  }

  if (draw === null) {
    return (
      <section className="draw-section">
        <h3>오늘의 뽑기</h3>
        {loadError && <p className="error">{loadError}</p>}
        <DrawForm groupId={groupId} onDrawn={handleDrawn} onConflict={handleConflict} />
      </section>
    )
  }

  const totalVotes = draw.candidates.reduce((sum, c) => sum + c.vote_count, 0)
  const isCreator = draw.created_by.id === myMemberId

  if (!isOpen) {
    const decided = draw.candidates.find((c) => c.restaurant_id === draw.decided_restaurant_id)
    return (
      <section className="draw-section">
        <h3>오늘의 뽑기 결과</h3>
        <div className="result">
          <span className="result-label">오늘의 점심</span>
          <span className="result-name">{decided?.name ?? '결정된 식당'}</span>
          {decided && <span className="badge">{CATEGORY_LABELS[decided.category]}</span>}
        </div>
        <VoteList candidates={draw.candidates} totalVotes={totalVotes} decidedId={draw.decided_restaurant_id} />
        <p className="hint">
          {decisionNote(draw.candidates)} {draw.created_by.nickname}님이 {formatKst(draw.closed_at)}에
          마감했어요.
        </p>
        <button type="button" onClick={() => setDraw(null)}>
          새로 뽑기
        </button>
      </section>
    )
  }

  const drawKey = `${draw.id}:${draw.round}`
  // 이미 투표했다면 다시 뒤집지 않아도 되게 모두 공개 상태로 본다.
  const revealedIds =
    draw.my_vote_restaurant_id !== null
      ? draw.candidates.map((c) => c.restaurant_id)
      : revealed.key === drawKey
        ? revealed.ids
        : []
  const allRevealed = draw.candidates.every((c) => revealedIds.includes(c.restaurant_id))

  function reveal(restaurantId) {
    setRevealed({ key: drawKey, ids: [...revealedIds, restaurantId] })
  }

  function vote(restaurantId) {
    mutate(`/groups/${groupId}/draws/${draw.id}/vote`, { method: 'PUT', body: { restaurant_id: restaurantId } })
  }

  function redraw() {
    if (!window.confirm('후보를 다시 뽑을까요? 지금 후보는 빠지고 모든 투표가 초기화돼요. (1회만 가능)')) return
    mutate(`/groups/${groupId}/draws/${draw.id}/redraw`, { method: 'POST' })
  }

  function close() {
    if (!window.confirm('투표를 마감할까요? 지금 득표로 오늘의 점심이 정해져요.')) return
    mutate(`/groups/${groupId}/draws/${draw.id}/close`, { method: 'POST' })
  }

  return (
    <section className="draw-section">
      <h3>오늘의 뽑기</h3>
      <p className="hint">
        {draw.created_by.nickname}님이 뽑은 후보 {draw.candidates.length}곳
        {draw.round > 1 && ' (다시 뽑음)'} · {revealedIds.length}장 공개 · 3초마다 갱신
      </p>
      {loadError && <p className="error">연결이 불안정해요. 다시 시도하는 중... ({loadError})</p>}
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

      {!allRevealed ? (
        <button type="button" className="primary vote-button" disabled>
          카드를 모두 공개하면 투표할 수 있어요
        </button>
      ) : (
        <VoteList
          candidates={draw.candidates}
          totalVotes={totalVotes}
          myVoteId={draw.my_vote_restaurant_id}
          onVote={vote}
          disabled={busy}
        />
      )}

      {actionError && (
        <p className="error" role="alert">
          {actionError}
        </p>
      )}

      {isCreator ? (
        <div className="creator-actions">
          {!draw.redraw_used && (
            <button type="button" onClick={redraw} disabled={busy}>
              다시 뽑기 (1회)
            </button>
          )}
          <button type="button" className="primary close-button" onClick={close} disabled={busy}>
            투표 마감하기
          </button>
        </div>
      ) : (
        <p className="hint">{draw.created_by.nickname}님이 마감하면 결과가 나와요.</p>
      )}
    </section>
  )
}

// 후보별 득표. onVote가 있으면 투표 버튼을, decidedId가 있으면 결정 표시를 보여 준다.
function VoteList({ candidates, totalVotes, myVoteId = null, onVote, disabled = false, decidedId = null }) {
  return (
    <ul className="vote-list" aria-label={`총 ${totalVotes}표`}>
      {candidates.map((c) => {
        const mine = c.restaurant_id === myVoteId
        const decided = c.restaurant_id === decidedId
        const percent = totalVotes === 0 ? 0 : Math.round((c.vote_count / totalVotes) * 100)
        return (
          <li key={c.restaurant_id} className={`vote-item${mine ? ' mine' : ''}${decided ? ' decided' : ''}`}>
            <div className="vote-row">
              <span className="vote-name">
                {decided && '🏆 '}
                {c.name}
              </span>
              <span className="vote-count">{c.vote_count}표</span>
              {onVote && (
                <button
                  type="button"
                  className={mine ? 'small primary' : 'small'}
                  onClick={() => onVote(c.restaurant_id)}
                  disabled={disabled || mine}
                  aria-pressed={mine}
                >
                  {mine ? '내 표' : '투표'}
                </button>
              )}
            </div>
            <div className="vote-bar" aria-hidden="true">
              <span style={{ width: `${percent}%` }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

export default DrawSection
