import { useState } from 'react'
import { useMutation } from '@apollo/client/react'
import {
  DELETE_TRANSACTION,
  UPDATE_TRANSACTION,
  refetchPortfolios,
} from '../api'
import { formatDate, formatMoney, formatShares } from '../format'

function TransactionRow({ transaction, isEditing, onEdit, onDone }) {
  const [type, setType] = useState(transaction.type)
  const [shares, setShares] = useState(String(transaction.shares))
  const [price, setPrice] = useState(String(transaction.price))
  const [message, setMessage] = useState(null)

  const [updateTransaction, { loading: saving }] = useMutation(
    UPDATE_TRANSACTION,
    refetchPortfolios,
  )
  const [deleteTransaction, { loading: deleting }] = useMutation(
    DELETE_TRANSACTION,
    refetchPortfolios,
  )

  const startEditing = () => {
    // Reset the draft to whatever is on screen before opening the editor.
    setType(transaction.type)
    setShares(String(transaction.shares))
    setPrice(String(transaction.price))
    setMessage(null)
    onEdit()
  }

  const handleSave = async () => {
    const parsedShares = parseFloat(shares)
    const parsedPrice = parseFloat(price)

    if (!Number.isFinite(parsedShares) || parsedShares <= 0) {
      setMessage('Shares must be a number greater than zero.')
      return
    }
    if (!Number.isFinite(parsedPrice) || parsedPrice < 0) {
      setMessage('Price must be zero or more.')
      return
    }

    try {
      await updateTransaction({
        variables: {
          id: parseInt(transaction.id, 10),
          type,
          shares: parsedShares,
          price: parsedPrice,
        },
      })
      onDone()
    } catch (err) {
      setMessage(err.message)
    }
  }

  const handleDelete = async () => {
    const confirmed = window.confirm(
      `Delete this ${transaction.type} of ${formatShares(transaction.shares)} shares?`,
    )
    if (!confirmed) return

    try {
      await deleteTransaction({
        variables: { id: parseInt(transaction.id, 10) },
      })
    } catch (err) {
      setMessage(err.message)
    }
  }

  if (isEditing) {
    return (
      <tr className="editing">
        <td>{formatDate(transaction.date)}</td>
        <td>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="BUY">Buy</option>
            <option value="SELL">Sell</option>
          </select>
        </td>
        <td className="num">
          <input
            className="cell-input"
            value={shares}
            onChange={(e) => setShares(e.target.value)}
          />
        </td>
        <td className="num">
          <input
            className="cell-input"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </td>
        <td className="num">—</td>
        <td className="num actions">
          <button onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button className="link-button" onClick={onDone} disabled={saving}>
            Cancel
          </button>
          {message && <p className="form-error">{message}</p>}
        </td>
      </tr>
    )
  }

  return (
    <tr>
      <td>{formatDate(transaction.date)}</td>
      <td>
        <span className={`tag tag-${transaction.type.toLowerCase()}`}>
          {transaction.type}
        </span>
      </td>
      <td className="num">{formatShares(transaction.shares)}</td>
      <td className="num">{formatMoney(transaction.price)}</td>
      <td className="num">
        {formatMoney(Number(transaction.shares) * Number(transaction.price))}
      </td>
      <td className="num actions">
        <button className="link-button" onClick={startEditing}>
          Edit
        </button>
        <button
          className="link-button danger"
          onClick={handleDelete}
          disabled={deleting}
        >
          {deleting ? 'Deleting…' : 'Delete'}
        </button>
        {message && <p className="form-error">{message}</p>}
      </td>
    </tr>
  )
}

export default TransactionRow
