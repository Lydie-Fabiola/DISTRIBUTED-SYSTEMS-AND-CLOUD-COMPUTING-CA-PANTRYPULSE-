import React, { useState } from 'react'

export default function Signup({ signupForm, setSignupForm, onSignup, navigate, goLogin }) {
  const [showPwd, setShowPwd] = useState(false)
  const [errors, setErrors] = useState({ password: '', email: '' })

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

  
  return (
    <div className="wrap auth">
      <header className="hero"><h1>KALY DRIVE</h1></header>
      <section className="card">
        <h2>Sign Up</h2>
        <div className="row">
          <input placeholder="Full name" autoComplete="off" value={signupForm.full_name} onChange={e=>{ const v=e.target.value; setSignupForm({...signupForm, full_name:v, login:v}) }} />
          <input type="email" placeholder="Email" autoComplete="off" value={signupForm.email} onChange={e=>setSignupForm({...signupForm, email:e.target.value})} onBlur={e=>validateField('email', e.target.value)} />
          <div className="pwd-field">
            <input className="pwd-input" type={showPwd?'text':'password'} placeholder="Password" autoComplete="new-password" value={signupForm.password} onChange={e=>setSignupForm({...signupForm, password:e.target.value})} onBlur={e=>validateField('password', e.target.value)} />
            <button type="button" className="icon-btn" aria-label={showPwd?'Hide password':'Show password'} onClick={()=>setShowPwd(v=>!v)}>
              {showPwd ? (
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8-11 8 11 8 11-8"/><circle cx="12" cy="12" r="3"/></svg>
              ) : (
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8-11 8 11 8 11-8"/><circle cx="12" cy="12" r="3"/><path d="M3 3l18 18"/></svg>
              )}
            </button>
          </div>
          <button className="primary" onClick={()=>{ if(!errors.password && !errors.email) onSignup() }}>
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="7" r="4"/><path d="M5.5 21a6.5 6.5 0 0 1 13 0"/><path d="M19 8l4 0"/><path d="M21 6l0 4"/></svg>
            Sign Up
          </button>
        </div>
        <div className="row">
          <div style={{minWidth:'50%'}}>{errors.password && (<div className="error">{errors.password}</div>)}</div>
          <div style={{minWidth:'50%'}}>{errors.email && (<div className="error">{errors.email}</div>)}</div>
        </div>
        <div className="row">
          <button onClick={()=> (goLogin ? goLogin() : navigate('/login'))}>
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/></svg>
            Back to Login
          </button>
        </div>
      </section>
    </div>
  )
}
