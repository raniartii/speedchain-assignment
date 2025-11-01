export default function BookingReview({ open, slots, onConfirm, onCancel }){
  if(!open) return null
  const { name, email, table_type, seats, slot_iso, meal = [], note = '' } = slots || {}
  const dt = slot_iso ? new Date(slot_iso) : null
  const when = dt ? dt.toLocaleString([], { dateStyle:'medium', timeStyle:'short' }) : '-'

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <h3 style={{marginTop:0}}>Confirm your booking</h3>
        <div className="review-grid">
          <div><span className="label">Name</span><div className="value">{name || '-'}</div></div>
          <div><span className="label">Email</span><div className="value">{email || '-'}</div></div>
          <div><span className="label">Table</span><div className="value">{table_type || '-'}</div></div>
          <div><span className="label">Seats</span><div className="value">{seats || '-'}</div></div>
          <div className="row2"><span className="label">When</span><div className="value">{when}</div></div>
          <div className="row2"><span className="label">Meal</span><div className="value">{(meal && meal.length)? meal.join(', ') : 'None'}</div></div>
          <div className="row2"><span className="label">Note</span><div className="value">{note || '-'}</div></div>
        </div>
        <div className="modal-actions">
          <button className="btn ghost" onClick={onCancel}>Edit</button>
          <button className="btn primary" onClick={onConfirm}>Confirm & Book</button>
        </div>
      </div>
    </div>
  )
}
