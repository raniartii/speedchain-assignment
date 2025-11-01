import { useEffect, useState } from 'react'
import { apiAvailabilityToday } from '../api'

function pctFill(value, max){ 
  const p = Math.max(0, Math.min(1, value / max))
  return `${Math.round(p*100)}%`
}

export default function AvailabilityPanel(){
  const [slots, setSlots] = useState([])
  const [cap, setCap] = useState({ small: 10, group: 4 })
  const [date, setDate] = useState('')

  useEffect(()=>{
    let mounted = true
    apiAvailabilityToday()
      .then(data => {
        if(!mounted) return
        setCap(data.capacity || cap)
        setDate(data.date)
        setSlots(data.slots || [])
      })
      .catch(()=>{})
    return ()=>{ mounted=false }
  }, [])

  return (
    <div className="card avail">
      <h3 style={{marginTop:0}}>Availability</h3>
      <div style={{color:'var(--muted)', fontSize:12, marginBottom:10}}>{date || 'Today'}</div>
      <div>
        {slots.map(s => {
          // for viz, compute fill by inverse of availability
          const smallLeft = s.available_small
          const groupLeft = s.available_group
          const smallFill = cap.small ? 1 - (smallLeft / cap.small) : 0
          const groupFill = cap.group ? 1 - (groupLeft / cap.group) : 0
          const t = new Date(s.slot_iso)
          const time = t.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
          return (
            <div className="slot" key={s.slot_iso}>
              <div className="time">{time}</div>
              <div className="bars">
                <div className="bar" title={`Small: ${smallLeft}/${cap.small} free`}>
                  <div className="fill" style={{width: pctFill(smallFill, 1)}}></div>
                </div>
                <span className="badge">S:{smallLeft}</span>
                <div className="bar" title={`Group: ${groupLeft}/${cap.group} free`}>
                  <div className="fill" style={{width: pctFill(groupFill, 1)}}></div>
                </div>
                <span className="badge">G:{groupLeft}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
