import { useMutation, useApolloClient } from '@apollo/client/react'
import { LOGOUT } from '../api'
import PortfolioList from './PortfolioList'

function Dashboard({ user }) {
  const client = useApolloClient()
  const [logout, { loading }] = useMutation(LOGOUT)

  const handleLogout = async () => {
    await logout()
    // Drops the cached portfolios and refetches `me`, which sends us back to
    // the login screen.
    await client.resetStore()
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>My Portfolios</h1>
        <div className="session">
          <span>
            Signed in as <strong>{user.username}</strong>
          </span>
          <button className="link-button" onClick={handleLogout} disabled={loading}>
            Log out
          </button>
        </div>
      </header>

      <PortfolioList />
    </div>
  )
}

export default Dashboard
