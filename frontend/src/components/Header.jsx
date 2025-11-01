import aiLogo from '../assets/ai-logo.svg'

export default function Header({ onOpenChat }){
  return (
    <div className="nav">
      <div className="brand">
        <img src={aiLogo} alt="AI" width="28" height="28" />
        <div>
          BrewHub Café
          <div className="tag">AI Receptionist</div>
        </div>
      </div>
      <button className="cta" onClick={onOpenChat}>
        <img src={aiLogo} alt="AI" width="18" height="18"/>
        Chat with AI
      </button>
    </div>
  )
}
