import { useQuery } from '@apollo/client/react'
import { ME } from './api'
import LoginForm from './components/LoginForm'
import Dashboard from './components/Dashboard'

function App() {
  const { loading, error, data, refetch } = useQuery(ME)

  if (loading) return <p className="status">Loading…</p>
  if (error) {
    return (
      <p className="status status-error">
        Could not reach the server: {error.message}
      </p>
    )
  }

  // Everything below the gate assumes a logged-in user; the API returns
  // nothing for anonymous requests anyway.
  if (!data?.me) return <LoginForm onLoggedIn={refetch} />

  return <Dashboard user={data.me} />
}

export default App
