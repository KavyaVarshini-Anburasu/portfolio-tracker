import { useState } from 'react'
import { useMutation } from '@apollo/client/react'
import { ADD_TRANSACTION, refetchPortfolios } from '../api'
import { formatShares } from '../format'

function AddTransactionForm({ holdings }) {
  const [holdingId, setHoldingId] = useState(holdings[0]?.id ?? '')
  const [type, setType] = useState('BUY')
  const [shares, setShares] = useState('')
  const [price, setPrice] = useState('')
  const [message, setMessage] = useState(null)

  const [addTransaction, { loading }] = useMutation(
    ADD_TRANSACTION,
    refetchPortfolios,
  )

  if (holdings.length === 0) return null

  // Surfaced as a hint only. The server owns the "can't oversell" rule; copying
  // it here would give us two places for it to drift.
  const selected = holdings.find((h) => String(h.id) === String(holdingId))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage(null)

    const parsedShares = parseFloat(shares)
    const parsedPrice = parseFloat(price)

    if (!holdingId) {
      setMessage('Pick a holding.')
      return
    }
    if (!Number.isFinite(parsedShares) || parsedShares <= 0) {
      setMessage('Shares must be a number greater than zero.')
      return
    }
    if (!Number.isFinite(parsedPrice) || parsedPrice < 0) {
      setMessage('Price must be zero or more.')
      return
    }

    try {
      await addTransaction({
        variables: {
          holdingId: parseInt(holdingId, 10),
          type,
          shares: parsedShares,
          price: parsedPrice,
        },
      })
      // Only clear once the refetch has landed, so the numbers above have
      // already moved when the inputs empty out.
      setShares('')
      setPrice('')
    } catch (err) {
      setMessage(err.message)
    }
  }

  return (
    <form className="add-transaction" onSubmit={handleSubmit}>
      <h3>Add transaction</h3>

      <div className="fields">
        <label>
          <span>Holding</span>
          <select
            value={holdingId}
            onChange={(e) => setHoldingId(e.target.value)}
          >
            {holdings.map((holding) => (
              <option key={holding.id} value={holding.id}>
                {holding.ticker}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Type</span>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="BUY">Buy</option>
            <option value="SELL">Sell</option>
          </select>
        </label>

        <label>
          <span>
            Shares
            {type === 'SELL' && selected
              ? ` (${formatShares(selected.shares)} held)`
              : ''}
          </span>
          <input
            inputMode="decimal"
            placeholder="0"
            value={shares}
            onChange={(e) => setShares(e.target.value)}
          />
        </label>

        <label>
          <span>Price</span>
          <input
            inputMode="decimal"
            placeholder="0.00"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? 'Adding…' : 'Add'}
        </button>
      </div>

      {message && <p className="form-error">{message}</p>}
    </form>
  )
}

export default AddTransactionForm
