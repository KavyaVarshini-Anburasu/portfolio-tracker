import { formatMoney } from '../format'
import HoldingsTable from './HoldingsTable'
import AddTransactionForm from './AddTransactionForm'

function PortfolioCard({ portfolio }) {
  return (
    <section className="card">
      <header className="card-header">
        <h2>{portfolio.name}</h2>
        <div className="card-total">
          <span className="label">Portfolio value</span>
          <span className="amount">{formatMoney(portfolio.totalValue)}</span>
        </div>
      </header>

      <HoldingsTable holdings={portfolio.holdings} />
      <AddTransactionForm holdings={portfolio.holdings} />
    </section>
  )
}

export default PortfolioCard
