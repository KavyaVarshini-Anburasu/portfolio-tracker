import { useState } from 'react'
import TransactionRow from './TransactionRow'

function TransactionHistory({ holding }) {
  const [editingId, setEditingId] = useState(null)

  if (holding.transactions.length === 0) {
    return <p className="empty">No transactions for {holding.ticker} yet.</p>
  }

  return (
    <div className="history">
      <h3>{holding.ticker} transactions</h3>
      <table className="transactions">
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th className="num">Shares</th>
            <th className="num">Price</th>
            <th className="num">Total</th>
            <th className="num">Actions</th>
          </tr>
        </thead>
        <tbody>
          {holding.transactions.map((transaction) => (
            <TransactionRow
              key={transaction.id}
              transaction={transaction}
              isEditing={editingId === transaction.id}
              onEdit={() => setEditingId(transaction.id)}
              onDone={() => setEditingId(null)}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default TransactionHistory
