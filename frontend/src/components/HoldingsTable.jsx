import { Fragment, useState } from 'react'
import { formatMoney, formatShares } from '../format'
import TransactionHistory from './TransactionHistory'

function HoldingsTable({ holdings }) {
  const [openHoldingId, setOpenHoldingId] = useState(null)

  if (holdings.length === 0) {
    return <p className="empty">No holdings in this portfolio yet.</p>
  }

  return (
    <table className="holdings">
      <thead>
        <tr>
          <th>Ticker</th>
          <th className="num">Shares</th>
          <th className="num">Price</th>
          <th className="num">Value</th>
          <th className="num">History</th>
        </tr>
      </thead>
      <tbody>
        {holdings.map((holding) => {
          const isOpen = openHoldingId === holding.id
          const count = holding.transactions.length

          return (
            <Fragment key={holding.id}>
              <tr>
                <td className="ticker">{holding.ticker}</td>
                <td className="num">{formatShares(holding.shares)}</td>
                <td className="num">{formatMoney(holding.currentPrice)}</td>
                <td className="num strong">{formatMoney(holding.value)}</td>
                <td className="num">
                  <button
                    className="link-button"
                    aria-expanded={isOpen}
                    onClick={() => setOpenHoldingId(isOpen ? null : holding.id)}
                  >
                    {count} {count === 1 ? 'transaction' : 'transactions'}
                  </button>
                </td>
              </tr>

              {isOpen && (
                <tr className="history-row">
                  <td colSpan={5}>
                    <TransactionHistory holding={holding} />
                  </td>
                </tr>
              )}
            </Fragment>
          )
        })}
      </tbody>
    </table>
  )
}

export default HoldingsTable
