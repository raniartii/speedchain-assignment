// MediaRecorder helpers for WebM/Opus
export class MicRecorder {
  constructor(){
    this.mediaStream = null;
    this.recorder = null;
    this.chunks = [];
  }
  async start(){
    this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.chunks = [];
    this.recorder = new MediaRecorder(this.mediaStream, { mimeType: 'audio/webm' });
    this.recorder.ondataavailable = e => { if(e.data && e.data.size > 0) this.chunks.push(e.data); };
    this.recorder.start();
  }
  async stop(){
    if(!this.recorder) return null;
    await new Promise(resolve => {
      this.recorder.onstop = resolve;
      this.recorder.stop();
    });
    this.mediaStream.getTracks().forEach(t => t.stop());
    const blob = new Blob(this.chunks, { type: 'audio/webm' });
    const file = new File([blob], `input-${Date.now()}.webm`, { type: 'audio/webm' });
    return file;
  }
}

export function playBase64Mp3(b64){
  if(!b64) return;
  const audio = new Audio(`data:audio/mpeg;base64,${b64}`);
  // Don’t block UI on play promise; ignore errors (autoplay policy)
  audio.play().catch(()=>{});
}
