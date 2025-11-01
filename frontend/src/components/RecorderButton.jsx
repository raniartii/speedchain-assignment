import { useEffect, useState } from 'react'
import { MicRecorder } from '../utils/audio'

export default function RecorderButton({ onTranscribed }){
  const [rec, setRec] = useState(null)
  const [recording, setRecording] = useState(false)
  const [label, setLabel] = useState('Tap to Record')
  const [busy, setBusy] = useState(false)   // <-- define hook at top level (NOT inside a function)

  useEffect(() => {
    setRec(new MicRecorder())
  }, [])

  const toggle = async () => {
    if (busy || !rec) return

    if (!recording) {
      try {
        setBusy(true)
        await rec.start()
        setRecording(true)
        setLabel('Recording... Tap to stop')
      } catch (e) {
        setLabel('Mic blocked. Allow microphone.')
      } finally {
        setBusy(false)
      }
    } else {
      try {
        setBusy(true)
        const voiceFile = await rec.stop()   // <-- stop ONCE; no duplicate const/file
        setRecording(false)
        setLabel('Processing...')

        if (voiceFile) {
          await onTranscribed(voiceFile)
          setLabel('Tap to Record')
        } else {
          setLabel('No audio captured')
        }
      } catch (e) {
        setLabel('Transcription failed')
      } finally {
        setBusy(false)
      }
    }
  }

  return (
    <div className="recorder">
      <button
        className={`rec-btn ${recording ? 'recording' : ''}`}
        onClick={toggle}
        disabled={busy}
        aria-busy={busy}
        title={label}
      >
        {recording ? 'STOP' : (busy ? '...' : 'RECORD')}
      </button>
      <div className="rec-label">{label}</div>
    </div>
  )
}
