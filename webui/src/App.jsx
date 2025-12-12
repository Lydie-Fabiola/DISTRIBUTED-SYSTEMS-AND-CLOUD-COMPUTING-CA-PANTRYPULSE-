import { useEffect, useRef, useState, useMemo } from 'react'
import { useNavigate, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import './App.css'

const API = 'http://127.0.0.1:8081'

function App() {
  const [userId, setUserId] = useState('')
  
  
  const [theme, setTheme] = useState('dark')
  const [quota, setQuota] = useState(null)
  const [objects, setObjects] = useState([])
  const [path, setPath] = useState('')
  const [prefix, _SET_PREFIX] = useState('')
  const [allowDup, setAllowDup] = useState(false)
  const [result, setResult] = useState('')
  const [showSidebar, setShowSidebar] = useState(true)
  const [loginForm, setLoginForm] = useState({login:'', password:'', email:''})
  const [awaitingOtp, setAwaitingOtp] = useState(false)
  const [otpCode, setOtpCode] = useState('')
  const [pendingUserId, setPendingUserId] = useState('')
  const [pendingUserEmail, setPendingUserEmail] = useState('')
  const [userEmail, setUserEmail] = useState('')
  const [recentOpen, setRecentOpen] = useState([])
  const [trashObjects, setTrashObjects] = useState([])
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [showAddAccount, setShowAddAccount] = useState(false)
  const [addAccountForm, setAddAccountForm] = useState({ full_name:'', email:'', password:'' })
  const [planPeriod, setPlanPeriod] = useState('monthly')
  
  const [loginError, setLoginError] = useState('')
  const [otpError, setOtpError] = useState('')
  const [otpInfo, setOtpInfo] = useState('')
  const [loadingLogin, setLoadingLogin] = useState(false)
  const [loadingOtp, setLoadingOtp] = useState(false)
  const [signupForm, setSignupForm] = useState({login:'', password:'', email:'', full_name:''})
  const [toasts, setToasts] = useState([])
  const progressRef = useRef(null)
  
  const navigate = useNavigate()
  const location = useLocation()

  async function refresh(uid = userId, pref = prefix) {
    const q = await fetch(`${API}/api/quota?user_id=${encodeURIComponent(uid)}`).then(r=>r.json())
    const l = await fetch(`${API}/api/list?user_id=${encodeURIComponent(uid)}&prefix=${encodeURIComponent(pref)}`).then(r=>r.json())
    setQuota(q)
    setObjects(l.objects || [])
  }

  useEffect(() => { document.body.className = theme==='light' ? 'theme-light' : '' }, [theme])
  
  function formatGB(mb) { if (mb === undefined || mb === null) return ''; const gb = mb / 1024; const t = gb >= 10 ? gb.toFixed(1) : gb.toFixed(2); return `${t} GB` }
  const folders = useMemo(() => {
    const s = new Set([''])
    for (const o of (objects || [])) {
      const p = o.path || ''
      if (!p.includes('/')) continue
      const parts = p.split('/')
      const dirs = parts.slice(0, -1)
      for (let i = 1; i <= dirs.length; i++) {
        s.add(dirs.slice(0, i).join('/'))
      }
    }
    return Array.from(s).sort()
  }, [objects])

  function uploadFile(file) {
    const fd = new FormData()
    fd.append('user_id', userId)
    fd.append('file', file)
    fd.append('path', path)
    fd.append('allow_duplicate', allowDup ? 'true' : 'false')
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API}/api/upload`)
    xhr.upload.onprogress = (evt) => {
      if (evt.lengthComputable && progressRef.current) {
        const pct = Math.round((evt.loaded/evt.total)*100)
        progressRef.current.style.width = pct + '%'
      }
    }
    xhr.onload = async () => {
      if (progressRef.current) progressRef.current.style.width = '0%'
      try { setResult(xhr.responseText) } catch { setResult('') }
      await refresh()
    }
    xhr.send(fd)
  }

  async function openFileAtPath(p) {
    try {
      const r = await fetch(`${API}/api/download?user_id=${encodeURIComponent(userId)}&path=${encodeURIComponent(p)}`)
      const b = await r.blob()
      const url = URL.createObjectURL(b)
      window.open(url, '_blank')
      setRecentOpen((prev)=>{
        const next = [{ path: p, at: Date.now() }, ...prev.filter(x=>x.path!==p)]
        return next.slice(0, 50)
      })
    } catch (e) { console.error(e) }
  }

  async function moveToTrash(p) {
    try {
      const r = await fetch(`${API}/api/download?user_id=${encodeURIComponent(userId)}&path=${encodeURIComponent(p)}`)
      if (!r.ok) return
      const b = await r.blob()
      const fd = new FormData()
      fd.append('user_id', userId)
      fd.append('file', b, p.split('/').pop())
      fd.append('path', `trash/${p}`)
      fd.append('allow_duplicate', 'false')
      await fetch(`${API}/api/upload`, { method:'POST', body: fd })
      await fetch(`${API}/api/object?user_id=${encodeURIComponent(userId)}&path=${encodeURIComponent(p)}`, { method:'DELETE' })
      await refresh()
    } catch (e) { console.error(e) }
  }

  async function refreshTrash() {
    const l = await fetch(`${API}/api/list?user_id=${encodeURIComponent(userId)}&prefix=${encodeURIComponent('trash')}`).then(r=>r.json())
    setTrashObjects(l.objects||[])
  }

  async function restoreFromTrash(p) {
    try {
      const r = await fetch(`${API}/api/download?user_id=${encodeURIComponent(userId)}&path=${encodeURIComponent(p)}`)
      if (!r.ok) return
      const b = await r.blob()
      const original = p.startsWith('trash/') ? p.slice(6) : p
      const fd = new FormData()
      fd.append('user_id', userId)
      fd.append('file', b, original.split('/').pop())
      fd.append('path', original)
      fd.append('allow_duplicate', 'false')
      await fetch(`${API}/api/upload`, { method:'POST', body: fd })
      await fetch(`${API}/api/object?user_id=${encodeURIComponent(userId)}&path=${encodeURIComponent(p)}`, { method:'DELETE' })
      await refresh()
      await refreshTrash()
    } catch (e) { console.error(e) }
  }

  if (!userId) {
    function addToast(type, text) { setToasts((ts)=>{ const id=Date.now()+Math.random(); const t=[...ts,{id,type,text}]; setTimeout(()=>{ setToasts((cur)=>cur.filter(x=>x.id!==id)) }, 4000); return t }) }
    async function onLogin() {
      setLoginError(''); setOtpError(''); setOtpInfo('');
      if(!loginForm.login || !loginForm.password || !loginForm.email){ setLoginError('All fields are required'); addToast('error','All fields are required'); return }
      setLoadingLogin(true)
      try {
        const r = await fetch(`${API}/api/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(loginForm)})
        if(r.ok){
          const j=await r.json(); setPendingUserId(j.user_id); setPendingUserEmail(j.email||loginForm.email); setAwaitingOtp(true)
          const er = await fetch(`${API}/api/enroll`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:loginForm.email, user_id: j.user_id})})
          if(er.ok){ const ej = await er.json(); const hint = ej.otp_hint ? ` (dev: ${ej.otp_hint})` : ''; const msg = (ej.message || 'OTP sent') + hint; setOtpInfo(msg); addToast('success', msg) }
          else { const ej = await er.json(); const wait = ej.retry_after||60; const msg = `Too many requests. Try in ${wait}s`; setOtpInfo(msg); addToast('error', msg) }
        } else { setLoginError('Invalid credentials'); addToast('error','Invalid credentials') }
      } catch { setLoginError('Network error'); addToast('error','Network error') } finally { setLoadingLogin(false) }
    }
    async function onVerify() {
      setOtpError(''); if(!otpCode){ setOtpError('Enter the OTP code'); addToast('error','Enter the OTP code'); return }
      setLoadingOtp(true)
      try {
        const vr = await fetch(`${API}/api/verify_login_otp`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:loginForm.email, otp_code: otpCode, user_id: pendingUserId})})
        if(vr.ok){ await vr.json(); setUserId(pendingUserId); setUserEmail(pendingUserEmail||loginForm.email); setAwaitingOtp(false); setOtpCode(''); setLoginForm({login:'',password:'',email:''}); setLoginError(''); setOtpError(''); setOtpInfo(''); setPendingUserId(''); setPendingUserEmail(''); navigate('/dashboard'); await refresh(pendingUserId); addToast('success','Welcome to KALY') }
        else {
          let msg = 'Invalid OTP'
          try {
            const t = await vr.text(); const ej = JSON.parse(t||'{}')
            if(ej.result==='ATTEMPT_BLOCKED'){ const wait = ej.retry_after||30; msg = `Too many attempts. Try in ${wait}s` }
            else if(ej.result==='EXPIRED'){ msg = 'OTP expired. Request a new code' }
          } catch (e) { console.error(e) }
          setOtpError(msg); addToast('error', msg)
        }
      } catch { setOtpError('Network error'); addToast('error','Network error') } finally { setLoadingOtp(false) }
    }
    async function onResend() {
      const er = await fetch(`${API}/api/enroll`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:loginForm.email})})
      if(er.ok){ const ej = await er.json(); const hint = ej.otp_hint ? ` (dev: ${ej.otp_hint})` : ''; const msg = 'OTP resent' + hint; setOtpInfo(msg); addToast('success', msg) }
      else { const ej = await er.json(); if(ej.result==='RESEND_LIMIT_REACHED'){ const msg = ej.message || 'Resend limit reached'; setOtpInfo(msg); addToast('error', msg) } else { const wait = ej.retry_after||60; const msg = `Too many requests. Try in ${wait}s`; setOtpInfo(msg); addToast('error', msg) } }
    }
    function goSignup() { setSignupForm({login:'',password:'',email:'',full_name:''}); navigate('/signup') }
    function goLogin() { setLoginForm({login:'',password:'',email:''}); setAwaitingOtp(false); setOtpCode(''); setLoginError(''); setOtpError(''); setOtpInfo(''); setPendingUserId(''); navigate('/login') }
    return (
      <>
        <Routes>
          <Route path="/login" element={<Login loginForm={loginForm} setLoginForm={setLoginForm} awaitingOtp={awaitingOtp} otpCode={otpCode} setOtpCode={setOtpCode} loadingLogin={loadingLogin} loadingOtp={loadingOtp} loginError={loginError} otpError={otpError} otpInfo={otpInfo} onLogin={onLogin} onVerify={onVerify} onResend={onResend} navigate={navigate} goSignup={goSignup} />} />
          <Route path="/signup" element={<Signup signupForm={signupForm} setSignupForm={setSignupForm} onSignup={async()=>{ const r = await fetch(`${API}/api/signup`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...signupForm, storage_limit_mb:5120})}); const j = await r.json(); if(j.result==='SUCCESS'){ setSignupForm({login:'',password:'',email:'',full_name:''}); addToast('success','Account created'); goLogin() } else { addToast('error', j.message||'Signup failed') } }} navigate={navigate} addToast={(type,text)=>addToast(type,text)} goLogin={goLogin} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
        <div className="toasts">{toasts.map(t=> (<div key={t.id} className={`toast ${t.type}`}>{t.type==='success'?<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>:<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v8"/><path d="M12 16h.01"/></svg>}<span>{t.text}</span></div>))}</div>
      </>
    )
  }

  return (
    <div className="wrap">
      <header className="hero">
        <div className="brand">
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7h13l5 5v7a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"/><path d="M8 7l4-4 4 4"/></svg>
          <h1>KALY DRIVE</h1>
        </div>
        <div className="user" style={{position:'relative'}}>
          <button className="icon-btn" onClick={()=>setShowProfileMenu(v=>!v)} aria-label="Profile Menu">
            <div className="avatar" title={userEmail||''}>{(userEmail||'').slice(0,1).toUpperCase()}</div>
          </button>
          {showProfileMenu && (
            <div className="profile-menu">
              <div style={{marginBottom:'8px'}}>{userEmail||'No email'}</div>
              <button onClick={()=>{ setShowAddAccount(true); setShowProfileMenu(false) }}>
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5a7 7 0 1 0 0 14"/><path d="M12 8v8"/><path d="M8 12h8"/></svg>
                Add account
              </button>
            </div>
          )}
          <label>User ID</label>
          <input value={userId} onChange={(e)=>setUserId(e.target.value)} />
          <button onClick={()=>{ setUserId(''); navigate('/login') }}>
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>
            Logout
          </button>
          <button onClick={()=>setShowSidebar(!showSidebar)}>
            {showSidebar ? (
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s4-8 10-8 10 8-10 8 10 8 10-8"/><path d="M12 12v0"/></svg>
            ) : (
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s4-8 10-8 10 8-10 8 10 8 10-8"/><path d="M3 3l18 18"/></svg>
            )}
            {showSidebar?'Hide':'Show'} Menu
          </button>
        </div>
      </header>
      {showAddAccount && (
        <div className="modal" role="dialog" aria-modal="true">
          <section className="card" style={{maxWidth:'520px', width:'100%'}}>
            <h2>Add Account</h2>
            <div className="row">
              <input placeholder="Full name" value={addAccountForm.full_name} onChange={e=>{ const v=e.target.value; setAddAccountForm({...addAccountForm, full_name:v}) }} />
              <input type="email" placeholder="Email" value={addAccountForm.email} onChange={e=>setAddAccountForm({...addAccountForm, email:e.target.value})} />
              <input type="password" placeholder="Password" value={addAccountForm.password} onChange={e=>setAddAccountForm({...addAccountForm, password:e.target.value})} />
              <button className="primary" onClick={async()=>{
                const body = { login: addAccountForm.full_name, full_name: addAccountForm.full_name, email: addAccountForm.email, password: addAccountForm.password, storage_limit_mb: 5120 }
                const r = await fetch(`${API}/api/signup`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) })
                const j = await r.json()
                if(j.result==='SUCCESS'){ setAddAccountForm({ full_name:'', email:'', password:'' }); setShowAddAccount(false); setToasts((ts)=>[...ts,{id:Date.now()+Math.random(),type:'success',text:'Account created'}]) }
                else { setToasts((ts)=>[...ts,{id:Date.now()+Math.random(),type:'error',text:j.message||'Failed to create account'}]) }
              }}>
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="7" r="4"/><path d="M5.5 21a6.5 6.5 0 0 1 13 0"/><path d="M19 8l4 0"/><path d="M21 6l0 4"/></svg>
                Sign Up
              </button>
              <button onClick={()=>setShowAddAccount(false)}>
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/></svg>
                Close
              </button>
            </div>
          </section>
        </div>
      )}
      {showSidebar && (
        <section className="sidebar">
          <div className="menu">
            <button className={location.pathname.startsWith('/dashboard')?'active':''} onClick={()=>{ navigate('/dashboard'); refresh() }}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
              Dashboard
            </button>
            <button className={location.pathname.startsWith('/upload')?'active':''} onClick={()=>navigate('/upload')}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 15v4a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4"/><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/></svg>
              Upload
            </button>
            <button className={location.pathname.startsWith('/files')?'active':''} onClick={()=>navigate('/files')}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7h13l5 5v7a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"/></svg>
              Files
            </button>
            <button className={location.pathname.startsWith('/recent')?'active':''} onClick={()=>navigate('/recent')}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-9-9"/><path d="M12 7v6l4 2"/></svg>
              Recent
            </button>
            <button className={location.pathname.startsWith('/trash')?'active':''} onClick={()=>{ navigate('/trash'); refreshTrash() }}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6l1-2h4l1 2"/></svg>
              Trash
            </button>
            <button className={location.pathname.startsWith('/storage')?'active':''} onClick={()=>navigate('/storage')}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 12V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v5"/><path d="M2 12h20"/><path d="M6 16h.01"/><path d="M10 16h.01"/><path d="M14 16h.01"/><path d="M18 16h.01"/></svg>
              Storage
            </button>
            <button className={location.pathname.startsWith('/sessions')?'active':''} onClick={()=>navigate('/sessions')}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 1 0-5-5"/><path d="M22 12h-4"/><path d="M2 12h4"/><path d="M12 22v-4"/></svg>
              Sessions
            </button>
            <button className={location.pathname.startsWith('/settings')?'active':''} onClick={()=>navigate('/settings')}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V22a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H2a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1A2 2 0 1 1 6.1 3.7l.1.1a1.7 1.7 0 0 0 1.8.3 1.7 1.7 0 0 0 1-1.5V2a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8 1.7 1.7 0 0 0 1.5 1H22a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1z"/></svg>
              Settings
            </button>
          </div>
        </section>
      )}

      <section className="content">
        <Routes>
          <Route path="/dashboard" element={(
            <section className="stats stats-anchor">
              <div className="card">
                <h3>Welcome to KALY</h3>
                <div>Glad to have you back.</div>
              </div>
              <div className="card">
                <h3>Your Quota</h3>
                {quota && (
                  <div>
                    <div>Limit: {formatGB(quota.limit_mb)}</div>
                    <div>Used: {formatGB(quota.used_mb)}</div>
                    <div>Remaining: {formatGB(quota.remaining_mb)}</div>
                  </div>
                )}
              </div>
              <div className="card">
                <h3>System Memory</h3>
                {quota && (
                  <div>
                    <div>Total: {formatGB(quota.system_total_mb)}</div>
                    <div>Used: {formatGB(quota.system_used_mb)}</div>
                    <div>Free: {formatGB(quota.system_free_mb)}</div>
                  </div>
                )}
              </div>
            </section>
          )} />
          <Route path="/upload" element={(
            <section className="card upload-anchor">
              <h2>Upload File</h2>
              <div className="row">
                <input type="file" onChange={e=>e.target.files[0] && uploadFile(e.target.files[0])} />
                <select value={path} onChange={e=>setPath(e.target.value)}>
                  <option value="">Root</option>
                  {folders.filter(f=>f).map(f=> (<option key={f} value={f}>{f}</option>))}
                </select>
                <label><input type="checkbox" checked={allowDup} onChange={e=>setAllowDup(e.target.checked)} /> Version on upload</label>
              </div>
              <div className="progress"><div ref={progressRef} className="bar"></div></div>
              <pre className="result">{result}</pre>
            </section>
          )} />
          <Route path="/files" element={(
            <section className="card files-anchor">
              <h2>Your Files</h2>
              
              <div className="list">
                <div className="list-head">
                  <div>Path</div><div>Size</div><div>Actions</div>
                </div>
                {(objects||[]).map(o=> (
                  <div className="list-row" key={o.path}>
                    <div>{o.path}</div>
                    <div>{formatGB(o.size_mb)}</div>
                    <div>
                      <button onClick={()=> openFileAtPath(o.path)}>
                        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7h13l5 5v7a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"/></svg>
                        Open
                      </button>
                      <button onClick={()=> window.location = `${API}/api/download?user_id=${encodeURIComponent(userId)}&path=${encodeURIComponent(o.path)}`}>
                        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/></svg>
                        Download
                      </button>
                      <button onClick={async ()=>{ await moveToTrash(o.path) }}>
                        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6l1-2h4l1 2"/></svg>
                        Move to Trash
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )} />
          <Route path="/recent" element={(
            <section className="card">
              <h2>Recently Opened</h2>
              <div className="list">
                <div className="list-head"><div>Path</div><div>Opened</div><div>Actions</div></div>
                {recentOpen.map(e=> (
                  <div className="list-row" key={e.path+String(e.at)}>
                    <div>{e.path}</div>
                    <div>{new Date(e.at).toLocaleString()}</div>
                    <div>
                      <button onClick={()=> openFileAtPath(e.path)}>
                        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7h13l5 5v7a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"/></svg>
                        Open
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )} />
          <Route path="/trash" element={(
            <section className="card">
              <h2>Trash</h2>
              <div className="row">
                <button onClick={()=>refreshTrash()}>
                  <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>
                  Refresh
                </button>
              </div>
              <div className="list">
                <div className="list-head"><div>Path</div><div>Size</div><div>Actions</div></div>
                {trashObjects.map(o=> (
                  <div className="list-row" key={o.path}>
                    <div>{o.path}</div>
                    <div>{formatGB(o.size_mb)}</div>
                    <div>
                      <button onClick={()=> restoreFromTrash(o.path)}>
                        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M23 4v6h-6"/><path d="M20 20a8 8 0 1 1 0-16"/></svg>
                        Restore
                      </button>
                      <button onClick={async ()=>{ await fetch(`${API}/api/object?user_id=${encodeURIComponent(userId)}&path=${encodeURIComponent(o.path)}`, {method:'DELETE'}); await refreshTrash(); }}>
                        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6l1-2h4l1 2"/></svg>
                        Delete Permanently
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )} />
          <Route path="/storage" element={(
            <section className="card">
              <h2>Storage</h2>
              {quota && (
                <div className="storage-header">
                  <div className="storage-bar">
                    <div className="bar" style={{width: `${Math.min(100, Math.round((quota.used_mb||0)/(quota.limit_mb||1)*100))}%`}}></div>
                  </div>
                  <div className="row">
                    <div>Used: {formatGB(quota.used_mb)}</div>
                    <div>Left: {formatGB(Math.max(0, (quota.limit_mb||0) - (quota.used_mb||0)))}</div>
                    <div>Total: {formatGB(quota.limit_mb)}</div>
                    <button className="primary" onClick={()=>{ const el = document.getElementById('plans'); if(el) el.scrollIntoView({behavior:'smooth', block:'start'}) }}>Get More Space</button>
                  </div>
                </div>
              )}
              <div className="row" style={{marginTop:'8px'}}>
                <label>Plan Period</label>
                <select onChange={e=>setPlanPeriod(e.target.value)} value={planPeriod}>
                  <option value="monthly">Monthly</option>
                  <option value="annual">Annual</option>
                </select>
              </div>
              <div id="plans" className="plans">
                {[
                  {label:'10 GB', mb:10240, priceMonthly:1500, priceAnnual:15000},
                  {label:'20 GB', mb:20480, priceMonthly:2500, priceAnnual:25000},
                  {label:'50 GB', mb:51200, priceMonthly:5000, priceAnnual:50000},
                  {label:'100 GB', mb:102400, priceMonthly:9000, priceAnnual:90000},
                ].map(p => (
                  <div key={p.mb} className="plan">
                    <div className="plan-title">{p.label}</div>
                    <div className="plan-price">{(planPeriod==='monthly'?p.priceMonthly:p.priceAnnual).toLocaleString()} FCFA / {planPeriod}</div>
                    <button className="primary" onClick={async()=>{
                      const price = planPeriod==='monthly'?p.priceMonthly:p.priceAnnual
                      const confirmed = window.confirm(`Pay ${price.toLocaleString()} FCFA (${planPeriod}) for ${p.label}?`)
                      if(!confirmed) return
                      const r = await fetch(`${API}/api/storage_limit`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ user_id: userId, limit_mb: p.mb }) })
                      const j = await r.json()
                      if(j.result==='SUCCESS'){ await refresh(userId); setToasts(ts=>[...ts,{id:Date.now()+Math.random(),type:'success',text:`Upgraded to ${p.label}`}]) }
                      else { setToasts(ts=>[...ts,{id:Date.now()+Math.random(),type:'error',text:j.message||'Payment failed'}]) }
                    }}>Pay</button>
                  </div>
                ))}
              </div>
            </section>
          )} />
          <Route path="/sessions" element={(
            <section className="card sessions-anchor">
              <h2>Sessions</h2>
              <button onClick={async()=>{ const j = await fetch(`${API}/api/sessions?user_id=${encodeURIComponent(userId)}`).then(r=>r.json()); setResult(JSON.stringify(j,null,2)) }}>
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-9-9"/><path d="M21 3v6h-6"/></svg>
                Refresh Sessions
              </button>
              <div className="list">
                <div className="list-head"><div>Token</div><div>Created</div><div>Actions</div></div>
                {(()=>{
                  try {
                    const j = JSON.parse(result||'{}')
                    return (j.sessions||[]).map(s=> (
                      <div className="list-row" key={s.token}>
                        <div style={{overflow:'hidden',textOverflow:'ellipsis'}}>{s.token}</div>
                        <div>{new Date((s.created_at||0)*1000).toLocaleString()}</div>
                        <div><button onClick={async()=>{ await fetch(`${API}/api/session?token=${encodeURIComponent(s.token)}`, {method:'DELETE'}); const j2 = await fetch(`${API}/api/sessions?user_id=${encodeURIComponent(userId)}`).then(r=>r.json()); setResult(JSON.stringify(j2,null,2)) }}>
                          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>
                          Logout
                        </button></div>
                      </div>
                    ))
                  } catch { return null }
                })()}
              </div>
            </section>
          )} />
          <Route path="/settings" element={(
            <section className="card">
              <h2>Settings</h2>
              <div className="row">
                <label>Theme</label>
                <button onClick={()=>setTheme(theme==='dark'?'light':'dark')}>
                  {theme==='dark' ? (
                    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
                  ) : (
                    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2"/><path d="M12 21v2"/><path d="M4.22 4.22l1.42 1.42"/><path d="M18.36 18.36l1.42 1.42"/><path d="M1 12h2"/><path d="M21 12h2"/><path d="M4.22 19.78l1.42-1.42"/><path d="M18.36 5.64l1.42-1.42"/></svg>
                  )}
                  {theme==='dark'?'Light':'Dark'} Mode
                </button>
              </div>
            </section>
          )} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </section>

    </div>
  )
}

export default App
