// The API returns decimals as strings (GraphQL Decimal scalar), so everything
// here coerces before formatting.

export function formatMoney(value) {
  return Number(value ?? 0).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  })
}

export function formatShares(value) {
  return Number(value ?? 0).toLocaleString('en-US', {
    maximumFractionDigits: 4,
  })
}

export function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
