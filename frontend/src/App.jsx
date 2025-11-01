import { useState } from 'react'
import './styles.css'
import Header from './components/Header'
import ChatUI from './components/ChatUI'
import AvailabilityPanel from './components/AvailabilityPanel'

export default function App(){
  const [showChat, setShowChat] = useState(false)

  return (
    <div className="container">
      <Header onOpenChat={() => setShowChat(true)} />

      {/* Landing hero */}
      {!showChat && (
        <section className="hero">
          <div className="card">
            <h1>Welcome to BrewHub Café ☕</h1>
            <p>
              Reserve cozy 2-seaters or team-ready group tables. Speak to our AI receptionist
              for quick bookings, availability, and confirmations — completely hands-free.
            </p>
            <div className="grid-2">
              <div className="kpi">
                <b>08:00–22:00</b><br/><span>Open hours (IST)</span>
              </div>
              <div className="kpi">
                <b>10 × 2-seaters</b><br/><span>Small tables</span>
              </div>
              <div className="kpi">
                <b>4 × 5-seaters</b><br/><span>Group tables</span>
              </div>
              <div className="kpi">
                <b>Voice-first</b><br/><span>STT → LLM → TTS</span>
              </div>
            </div>

            <div style={{marginTop:18}}>
              <button className="cta" onClick={() => setShowChat(true)}>
                Start Chatting with AI
              </button>
            </div>
          </div>

          <div className="card">
            <h3 style={{marginTop:0}}>Today at BrewHub</h3>
            <p style={{marginTop:6, color:'var(--muted)'}}>
              Check seat availability and jump into a quick booking from the chat.
            </p>
            <AvailabilityPanel />
          </div>
        </section>
      )}

      {/* Chat + Availability */}
      {showChat && (
        <section className="section">
          <ChatUI />
          <AvailabilityPanel />
        </section>
      )}

      <footer>© {new Date().getFullYear()} BrewHub Café — AI Receptionist Demo</footer>
    </div>
  )
}
