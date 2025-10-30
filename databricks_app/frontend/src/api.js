/**
 * API Configuration
 * Works with both local development and Databricks proxy
 */
import axios from 'axios'

// Create axios instance with relative base URL
// This works with Databricks driver-proxy and local development
const api = axios.create({
  baseURL: './',  // Relative to current location
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api

/**
 * WebSocket connection helper
 * Automatically handles Databricks proxy paths
 */
export function createWebSocket(path) {
  // Get the current location
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  
  // Build WebSocket URL relative to current page
  // Remove any trailing slashes from pathname
  let basePath = window.location.pathname.replace(/\/$/, '')
  
  // If we're on root, basePath is empty
  const wsUrl = basePath 
    ? `${protocol}//${host}${basePath}/${path}` 
    : `${protocol}//${host}/${path}`
  
  console.log(`WebSocket connecting to: ${wsUrl}`)
  
  return new WebSocket(wsUrl)
}

