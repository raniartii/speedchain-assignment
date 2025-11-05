import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'
import TypingDots from './TypingDots'
import RecorderButton from './RecorderButton'
import BookingReview from './BookingReview'
import { apiConverse, apiNewSession, apiTranscribe } from '../api'
import { playBase64Mp3 } from '../utils/audio'

function nowTime(){
  return new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
}

export default function ChatUI(){
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([
    { who:'ai', text:'Hi! I\'m your BrewHub Café assistant. Tap Record and tell me what you need.', time: nowTime() }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  // mirror of backend state (read-only for UI)
  const [slots, setSlots] = useState({ name:null, email:null, table_type:null, seats:null, slot_iso:null, meal:[], note:'' })
  const [awaitingConfirm, setAwaitingConfirm] = useState(false)
  const [showReview, setShowReview] = useState(false)

  const scrollRef = useRef(null)

  useEffect(()=>{
    const sid = localStorage.getItem('brewhub_sid')
    if(sid) {
      setSessionId(sid)
    } else {
      apiNewSession().then(r => {
        setSessionId(r.session_id)
        localStorage.setItem('brewhub_sid', r.session_id)
      })
    }
  }, [])

  useEffect(()=>{
    if(scrollRef.current){
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, loading, showReview])

  const appendAi = (text) => setMessages(m => [...m, { who:'ai', text, time: nowTime() }])
  const appendUser = (text) => setMessages(m => [...m, { who:'user', text, time: nowTime() }])

  const handleBackendReply = (resp) => {

    if (resp?.session_id && resp.session_id !== sessionId) {
      setSessionId(resp.session_id);
      try { localStorage.setItem('brewhub_sid', resp.session_id); } catch {}
    }

    // 1) show AI reply from backend (single source of truth)
    setMessages(m => [...m, { who:'ai', text: resp.reply_text, time: nowTime() }])

    // 2) play TTS if present
    if(resp.tts_audio_base64) playBase64Mp3(resp.tts_audio_base64)

    // 3) reflect backend state
    const s = resp?.state?.slots || {}
    setSlots(prev => ({ ...prev, ...s }))

    const awaiting = !!resp?.state?.awaiting_confirmation
    setAwaitingConfirm(awaiting)

    // 4) open review modal when backend asks to confirm
    if(awaiting) setShowReview(true)
  }

  const sendText = async (text) => {
    if(!text?.trim()) return
    appendUser(text)
    setInput('')
    setLoading(true)
    try{
      const r = await apiConverse(sessionId, text)
      await new Promise(res => setTimeout(res, 150))
      handleBackendReply(r)
    }catch(e){
      appendAi('Error contacting assistant.')
    }finally{
      setLoading(false)
    }
  }

  // Voice path with markers only (no extra prompting)
  const onTranscribed = async (file) => {
    appendUser('[ Voice Message Sent ]')
    let text = ''
    try{
      const raw = await apiTranscribe(file)
      text = (raw || '').trim()
      appendUser(text ? `Transcription: ${text}` : 'Transcription: [empty]')
    }catch{
      appendAi('Transcription failed.')
      return
    }
    if(!text) return
    setLoading(true)
    try{
      const r = await apiConverse(sessionId, text)
      await new Promise(res => setTimeout(res, 150))
      handleBackendReply(r)
    }catch{
      appendAi('Error contacting assistant.')
    }finally{
      setLoading(false)
    }
  }

  const onSubmit = (e) => {
    e.preventDefault()
    sendText(input)
  }

  // Review modal actions:
  // We now let the BACKEND perform booking on "yes" (it saves JSON + sends email).
  const handleConfirm = async () => {
    setShowReview(false)
    // send "yes" to backend FSM to book
    await sendText('yes')
  }

  return (
    <div className="card chat-wrap">
      <div ref={scrollRef} className="scroll">
        <div className="msg-list">
          {messages.map((m, i) => (
            <MessageBubble key={i} who={m.who} text={m.text} time={m.time} />
          ))}
          {loading && (<MessageBubble who="ai" text={<TypingDots/>} />)}
        </div>
      </div>

      <div>
        <form className="input-row" onSubmit={onSubmit}>
          <input
            className="input"
            placeholder="Answer or ask anything…"
            value={input}
            onChange={e => setInput(e.target.value)}
          />
          <button className="send" type="submit">Send</button>
        </form>
        <div style={{height:12}} />
        <RecorderButton onTranscribed={onTranscribed} />
        <div className="rec-label"></div>
      </div>

      {/* Review modal renders only when backend is awaiting confirmation */}
      <BookingReview
        open={showReview && awaitingConfirm}
        slots={slots}
        onConfirm={handleConfirm}
        onCancel={() => setShowReview(false)}
      />
    </div>
  )
}
