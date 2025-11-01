import { clsx } from 'clsx'

export default function MessageBubble({ who, text, time, children }){
  return (
    <div className={clsx('msg', who === 'user' ? 'user' : 'ai')}>
      <div>
        <div>{text}{children}</div>
        {time && <small>{time}</small>}
      </div>
    </div>
  )
}
