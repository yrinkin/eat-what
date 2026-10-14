// 입장 후 첫 화면. 식당 목록, 뽑기 등은 이후 작업에서 추가한다.
function HomePage({ me }) {
  return (
    <section className="home">
      <p className="greeting">
        <strong>{me.member.nickname}</strong>님, 반가워요.
      </p>
      <dl className="group-info">
        <dt>그룹</dt>
        <dd>{me.group.name}</dd>
        <dt>초대 코드</dt>
        <dd className="code">{me.group.invite_code}</dd>
      </dl>
      <p className="hint">팀원에게 초대 코드를 알려 주면 같은 그룹에 들어올 수 있어요.</p>
    </section>
  )
}

export default HomePage
