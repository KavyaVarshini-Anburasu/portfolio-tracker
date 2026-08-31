import { useQuery } from '@apollo/client/react'
import { GET_PORTFOLIOS } from '../api'
import { formatMoney } from '../format'
import PortfolioCard from './PortfolioCard'

function PortfolioList() {
  const { loading, error, data } = useQuery(GET_PORTFOLIOS)

  if (loading) return <p className="status">Loading portfolios…</p>
  if (error) return <p className="status status-error">{error.message}</p>

  const portfolios = data?.portfolios ?? []
  if (portfolios.length === 0) {
    return <p className="status">No portfolios yet.</p>
  }

  const grandTotal = portfolios.reduce(
    (sum, portfolio) => sum + Number(portfolio.totalValue),
    0,
  )

  return (
    <>
      <div className="grand-total">
        <span className="label">Total portfolio value</span>
        <span className="amount">{formatMoney(grandTotal)}</span>
      </div>

      <div className="portfolio-list">
        {portfolios.map((portfolio) => (
          <PortfolioCard key={portfolio.id} portfolio={portfolio} />
        ))}
      </div>
    </>
  )
}

export default PortfolioList
