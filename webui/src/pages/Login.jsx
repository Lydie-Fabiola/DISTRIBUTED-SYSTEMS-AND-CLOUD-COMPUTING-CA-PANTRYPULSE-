import React, { useState } from 'react'

export default function Login({ loginForm, setLoginForm, awaitingOtp, otpCode, setOtpCode, loadingLogin, loadingOtp, loginError, otpError, otpInfo, onLogin, onVerify, onResend, navigate, goSignup }) {
  const [showPwd, setShowPwd] = useState(false)
  const [errors, setErrors] = useState({ login: '', password: '', email: '' })

  function isValidEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
  }

  function validateField(name, value) {
    let msg = ''
    if (!value) msg = 'Required'
    else if (name === 'email' && !isValidEmail(value)) msg = 'Invalid email'
    setErrors(prev => ({ ...prev, [name]: msg }))
    return !msg
  }

  function validateAll() {
    const okLogin = validateField('login', loginForm.login)
    const okPwd = validateField('password', loginForm.password)
    const okEmail = validateField('email', loginForm.email)
    return okLogin && okPwd && okEmail
  }
  return (
    <div className="wrap auth">
      <header className="hero"><h1>KALY DRIVE</h1></header>
      <section className="card">
        <h2>Login</h2>
        <div className="row">
          <input placeholder="Username" autoComplete="off" value={loginForm.login} onChange={e=>setLoginForm({...loginForm, login:e.target.value})} onBlur={e=>validateField('login', e.target.value)} />
          <div className="pwd-field">
            <input className="pwd-input" type={showPwd?'text':'password'} placeholder="Password" autoComplete="new-password" value={loginForm.password} onChange={e=>setLoginForm({...loginForm, password:e.target.value})} onBlur={e=>validateField('password', e.target.value)} />
            <button type="button" className="icon-btn" aria-label={showPwd?'Hide password':'Show password'} onClick={()=>setShowPwd(v=>!v)}>
              {showPwd ? (
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8-11 8 11 8 11-8"/><circle cx="12" cy="12" r="3"/></svg>
              ) : (
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8-11 8 11 8 11-8"/><circle cx="12" cy="12" r="3"/><path d="M3 3l18 18"/></svg>
              )}
            </button>
          </div>
          <input type="email" placeholder="Email for OTP" autoComplete="off" value={loginForm.email} onChange={e=>setLoginForm({...loginForm, email:e.target.value})} onBlur={e=>validateField('email', e.target.value)} />
          <button className="primary" disabled={loadingLogin} onClick={()=>{ if(validateAll()) onLogin() }}>
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/></svg>
            Login
          </button>
        </div>
        <div className="row">
          <div style={{minWidth:'33%'}}>{errors.login && (<div className="error">{errors.login}</div>)}</div>
          <div style={{minWidth:'33%'}}>{errors.password && (<div className="error">{errors.password}</div>)}</div>
          <div style={{minWidth:'33%'}}>{errors.email && (<div className="error">{errors.email}</div>)}</div>
        </div>
        {loginError && (<div className="error">{loginError}</div>)}
        {otpInfo && (<div className="success">{otpInfo}</div>)}
        <div className="row">
          <button onClick={()=> (goSignup ? goSignup() : navigate('/signup'))}>Sign Up?</button>
        </div>
        {awaitingOtp && (
          <div className="row">
            <input placeholder="Enter OTP code" autoComplete="one-time-code" value={otpCode} onChange={e=>setOtpCode(e.target.value)} />
            <button disabled={loadingOtp} onClick={onVerify}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
              Verify
            </button>
            <button disabled={loadingOtp} onClick={onResend}>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M23 4v6h-6"/><path d="M20 20a8 8 0 1 1 0-16"/></svg>
              Resend Code
            </button>
          </div>
        )}
        {otpError && (<div className="error">{otpError}</div>)}
      </section>
    </div>
  )
}
