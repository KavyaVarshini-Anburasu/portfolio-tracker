import { useState } from 'react'
import { useMutation } from '@apollo/client/react'
import { LOGIN } from '../api'

function LoginForm({ onLoggedIn }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState(null)
  const [login, { loading }] = useMutation(LOGIN)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage(null)

    if (!username || !password) {
      setMessage('Enter a username and password.')
      return
    }

    try {
      const { data } = await login({ variables: { username, password } })
      if (data?.login) {
        setPassword('')
        onLoggedIn()
      } else {
        setMessage('That username and password did not match.')
        setPassword('')
      }
    } catch (err) {
      setMessage(err.message)
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Portfolio Tracker</h1>
        <p className="login-subtitle">Sign in to see your holdings.</p>

        <label htmlFor="username">Username</label>
        <input
          id="username"
          autoComplete="username"
          autoFocus
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button type="submit" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign in'}
        </button>

        {message && <p className="form-error">{message}</p>}
      </form>
    </div>
  )
}

export default LoginForm
