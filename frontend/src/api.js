import { gql } from '@apollo/client'

export const ME = gql`
  query Me {
    me {
      id
      username
    }
  }
`

export const GET_PORTFOLIOS = gql`
  query Portfolios {
    portfolios {
      id
      name
      totalValue
      holdings {
        id
        ticker
        currentPrice
        shares
        value
        transactions {
          id
          type
          shares
          price
          date
        }
      }
    }
  }
`

export const LOGIN = gql`
  mutation Login($username: String!, $password: String!) {
    login(username: $username, password: $password) {
      id
      username
    }
  }
`

export const LOGOUT = gql`
  mutation Logout {
    logout
  }
`

export const ADD_TRANSACTION = gql`
  mutation AddTransaction(
    $holdingId: Int!
    $type: String!
    $shares: Float!
    $price: Float!
  ) {
    addTransaction(
      holdingId: $holdingId
      type: $type
      shares: $shares
      price: $price
    ) {
      id
    }
  }
`

export const UPDATE_TRANSACTION = gql`
  mutation UpdateTransaction(
    $id: Int!
    $type: String!
    $shares: Float!
    $price: Float!
  ) {
    updateTransaction(id: $id, type: $type, shares: $shares, price: $price) {
      id
      type
      shares
      price
    }
  }
`

export const DELETE_TRANSACTION = gql`
  mutation DeleteTransaction($id: Int!) {
    deleteTransaction(id: $id)
  }
`

// Shares, holding value and portfolio total are all derived server-side from
// the transaction list, so any write has to re-read the portfolios query
// rather than patching the cache by hand.
export const refetchPortfolios = {
  refetchQueries: [{ query: GET_PORTFOLIOS }],
  awaitRefetchQueries: true,
}
