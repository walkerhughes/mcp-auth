import React, { useEffect, useRef, useState } from 'react'
import ReactDOM from 'react-dom/client'
import {
  IdentityProvider,
  Products,
  StytchLogin,
  StytchProvider,
  createStytchClient,
  useStytch,
  useStytchUser,
} from '@stytch/react'
import './style.css'

const stytch = createStytchClient(__STYTCH_PUBLIC_TOKEN__)

function Login() {
  const callback = `${window.location.origin}/authenticate`
  return (
    <main>
      <StytchLogin
        config={{
          products: [Products.emailMagicLinks],
          emailMagicLinksOptions: {
            loginRedirectURL: callback,
            signupRedirectURL: callback,
          },
          sessionOptions: { sessionDurationMinutes: 30 },
        }}
      />
    </main>
  )
}

function Authenticate() {
  const client = useStytch()
  const { user } = useStytchUser()
  const started = useRef(false)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (user) {
      const returnTo = sessionStorage.getItem('returnTo') || '/'
      sessionStorage.removeItem('returnTo')
      window.location.replace(returnTo)
      return
    }
    if (started.current) return
    started.current = true
    void client.authenticateByUrl({ session_duration_minutes: 30 }).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : 'Could not finish sign in')
    })
  }, [client, user])
  return <main><p>{error || 'Finishing sign in...'}</p></main>
}

function Authorize() {
  const { user, isInitialized } = useStytchUser()
  useEffect(() => {
    if (isInitialized && !user) {
      sessionStorage.setItem('returnTo', window.location.href)
      window.location.replace('/')
    }
  }, [isInitialized, user])
  if (!isInitialized || !user) return <main><p>Checking your session...</p></main>
  return <main><IdentityProvider /></main>
}

function App() {
  if (window.location.pathname === '/authenticate') return <Authenticate />
  if (window.location.pathname === '/oauth/authorize') return <Authorize />
  return <Login />
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><StytchProvider stytch={stytch}><App /></StytchProvider></React.StrictMode>,
)
