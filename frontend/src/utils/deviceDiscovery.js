/**
 * Prey Project-style Device Discovery
 * Discovers running agent device via localhost HTTP endpoint
 */

const AGENT_DISCOVERY_URL = 'http://127.0.0.1:9123/device-info'

export async function discoverLocalDevice() {
  /**
   * Discover device_id from running agent on localhost.
   * Returns device_id if agent is running.
   * In production (Vercel), this will always fail due to CORS,
   * which is expected and should not block registration.
   */

  // Skip discovery in production (Vercel) - can't access localhost
  if (import.meta.env.PROD || window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return {
      success: false,
      error: 'Device discovery not available in production',
      device_id: null
    }
  }

  try {
    const response = await fetch(AGENT_DISCOVERY_URL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      signal: AbortSignal.timeout(2000)
    })

    if (response.ok) {
      const data = await response.json()
      return {
        success: true,
        device_id: data.device_id,
        status: data.status
      }
    }
  } catch (error) {
    if (!import.meta.env.PROD) {
      console.log('[DEVICE-DISCOVERY] Agent not running or not accessible')
    }
    return {
      success: false,
      error: 'Agent not running or not accessible',
      device_id: null
    }
  }

  return {
    success: false,
    error: 'Unknown error',
    device_id: null
  }
}
