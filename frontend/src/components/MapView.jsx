import { useEffect, useRef, useMemo, useCallback } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { formatDateTime } from '../utils/dateFormatter'

/**
 * MapView component using OpenStreetMap + Leaflet instead of Google Maps.
 * 
 * Props:
 * - devices: array of device objects with last_lat/last_lng, status, is_missing, last_seen, name
 * - center: default map center { lat, lng }
 * - zoom: initial zoom level
 * - geofence: optional geofence object with center_lat, center_lng, radius_m, enabled
 */
const MapView = ({ devices, center = { lat: 3.139, lng: 101.686 }, zoom = 10, geofence = null }) => {
  const mapRef = useRef(null)
  const markersRef = useRef([])
  const geofenceCircleRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const initializedRef = useRef(false)

  // Memoize center to prevent unnecessary re-renders
  const mapCenter = useMemo(() => {
    if (devices.length > 0 && devices[0].last_lat && devices[0].last_lng) {
      // Ensure coordinates are numbers and in valid ranges
      const lat = Number(devices[0].last_lat)
      const lng = Number(devices[0].last_lng)
      // Validate coordinate ranges (lat: -90 to 90, lng: -180 to 180)
      if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        return { lat, lng }
      }
    }
    return center
  }, [devices.length > 0 ? devices[0]?.last_lat : null, devices.length > 0 ? devices[0]?.last_lng : null, center?.lat, center?.lng])

  // Memoize geofence object to prevent re-renders
  const geofenceMemo = useMemo(() => {
    if (!geofence || !geofence.enabled || !geofence.center_lat || !geofence.center_lng) return null
    return geofence
  }, [geofence?.enabled, geofence?.center_lat, geofence?.center_lng, geofence?.radius_m])

  // Function to update markers and geofence without recreating the map
  const updateMapContent = useCallback(() => {
    if (!mapInstanceRef.current || !initializedRef.current) return

    const map = mapInstanceRef.current

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove())
    markersRef.current = []
    
    // Add new markers
    devices.forEach(device => {
      console.log(`[MapView] Processing device for marker:`, {
        name: device.name,
        device_id: device.device_id,
        last_lat: device.last_lat,
        last_lng: device.last_lng,
        last_lat_type: typeof device.last_lat,
        last_lng_type: typeof device.last_lng,
        has_coordinates: !!(device.last_lat && device.last_lng),
        device_keys: Object.keys(device)
      })
      
      // Check for alternative location field names (handle various data formats)
      let lat = device.last_lat ?? device.lat ?? device.location?.lat
      let lng = device.last_lng ?? device.lng ?? device.location?.lng
      
      // Handle null/undefined explicitly - try alternative field names
      if (lat === null || lat === undefined || lng === null || lng === undefined) {
        // Try alternative field names with different casing
        lat = device.Last_lat ?? device.LAT ?? null
        lng = device.Last_lng ?? device.LNG ?? null
      }
      
      // Convert to numbers, handling string numbers
      // Reject 0,0 coordinates (invalid - in ocean off Africa)
      if (lat && lng && lat !== 0 && lng !== 0) {
        // Ensure coordinates are numbers and in valid ranges
        const latNum = typeof lat === 'string' ? parseFloat(lat) : Number(lat)
        const lngNum = typeof lng === 'string' ? parseFloat(lng) : Number(lng)
        
        // Reject if coordinates are still 0 after parsing
        if (latNum === 0 && lngNum === 0) {
          console.warn(`[MapView] Rejecting invalid coordinates (0,0) for device ${device.name}`)
          return
        }
        
        // Debug logging to verify coordinates
        console.log(`[MapView] Device ${device.name} coordinates:`, { 
          raw: { lat, lng },
          parsed: { lat: latNum, lng: lngNum },
          isValid: !isNaN(latNum) && !isNaN(lngNum) && latNum >= -90 && latNum <= 90 && lngNum >= -180 && lngNum <= 180
        })
        
        // CRITICAL: Validate and fix swapped coordinates globally
        // Latitude must be between -90 and 90, Longitude must be between -180 and 180
        let finalLat = latNum
        let finalLng = lngNum
        
        // Check if coordinates are swapped (common Windows Location API issue)
        // If lat is outside -90 to 90 range, it's definitely swapped
        if (isNaN(latNum) || isNaN(lngNum)) {
          console.warn(`Invalid coordinates (NaN) for device ${device.name}: lat=${lat}, lng=${lng}`)
          return
        }
        
        // Detect swapped coordinates: lat outside valid range
        if (latNum < -90 || latNum > 90) {
          // Latitude is invalid - coordinates are swapped
          console.warn(`[MapView] Detected swapped coordinates (lat out of range) for device ${device.name}!`, {
            received: { lat: latNum, lng: lngNum },
            corrected: { lat: lngNum, lng: latNum }
          })
          finalLat = lngNum
          finalLng = latNum
        } else if (lngNum < -180 || lngNum > 180) {
          // Longitude is invalid - coordinates are swapped
          console.warn(`[MapView] Detected swapped coordinates (lng out of range) for device ${device.name}!`, {
            received: { lat: latNum, lng: lngNum },
            corrected: { lat: lngNum, lng: latNum }
          })
          finalLat = lngNum
          finalLng = latNum
        } else {
          // Coordinates are in valid ranges, but check for common swap patterns
          // If lat is in typical lng range (e.g., 100-180) and lng is in typical lat range (e.g., -90 to 90)
          // This indicates a swap
          if ((latNum >= 100 && latNum <= 180 && Math.abs(lngNum) <= 90) || 
              (Math.abs(latNum) <= 90 && (lngNum >= 100 && lngNum <= 180))) {
            // Check if swapping makes more sense (both in valid ranges after swap)
            const swappedLat = lngNum
            const swappedLng = latNum
            if (swappedLat >= -90 && swappedLat <= 90 && swappedLng >= -180 && swappedLng <= 180) {
              console.warn(`[MapView] Detected swapped coordinates (pattern match) for device ${device.name}!`, {
                received: { lat: latNum, lng: lngNum },
                corrected: { lat: swappedLat, lng: swappedLng }
              })
              finalLat = swappedLat
              finalLng = swappedLng
            }
          }
        }
        
        // Final validation: ensure coordinates are in valid ranges
        if (finalLat < -90 || finalLat > 90 || finalLng < -180 || finalLng > 180) {
          console.warn(`Invalid coordinates after swap check for device ${device.name}: lat=${finalLat}, lng=${finalLng}`)
          return
        }
        
        // Choose marker color based on device status
        let markerColor = '#FF0000'
        if (device.status === 'active' && !device.is_missing) markerColor = '#00AA00'
        if (device.is_missing) markerColor = '#FF0000'
        if (device.status === 'locked') markerColor = '#FFA500'

        const markerLatLng = [finalLat, finalLng]
        console.log('[MapView] Creating marker at:', markerLatLng)

        // Use a larger, more visible circle marker with shadow for better visibility
        const marker = L.circleMarker(markerLatLng, {
          radius: 18,
          color: '#FFFFFF',
          weight: 4,
          fillColor: markerColor,
          fillOpacity: 1.0,
        }).addTo(map)
        
        // Ensure marker is always on top and visible
        marker.bringToFront()
        
        // Add pulsing animation for better visibility
        marker.on('add', function() {
          // Initial pulse animation
          setTimeout(() => {
            this.setStyle({ radius: 22, fillOpacity: 0.7 })
            setTimeout(() => {
              this.setStyle({ radius: 18, fillOpacity: 1.0 })
            }, 300)
          }, 100)
        })
        
        // Add click handler to ensure marker is interactive
        marker.on('click', function() {
          this.openPopup()
        })
        
        // Format last seen time properly
        const lastSeenFormatted = device.last_seen ? formatDateTime(device.last_seen) : 'N/A'
        
        const popupHtml = `
          <div style="padding: 8px; min-width: 200px;">
            <h3 style="font-weight: bold; margin-bottom: 4px;">${device.name}</h3>
            <p style="font-size: 12px; margin: 2px 0;">Status: <strong>${device.status || 'active'}</strong></p>
            <p style="font-size: 11px; color: #666; margin: 2px 0;">${device.device_type || 'Unknown Device'}</p>
            <p style="font-size: 11px; color: #999; margin: 2px 0;">Last seen: ${lastSeenFormatted}</p>
            <p style="font-size: 10px; color: #999; margin-top: 4px;">📍 ${finalLat.toFixed(6)}, ${finalLng.toFixed(6)}</p>
          </div>
        `

        marker.bindPopup(popupHtml)

        markersRef.current.push(marker)
      }
    })
    
    // Update geofence circle
    if (geofenceMemo && devices.length === 1) {
      if (geofenceCircleRef.current) {
        geofenceCircleRef.current.remove()
      }
      
      // Ensure geofence coordinates are numbers
      const geofenceLat = Number(geofenceMemo.center_lat)
      const geofenceLng = Number(geofenceMemo.center_lng)
      
      if (isNaN(geofenceLat) || isNaN(geofenceLng) || geofenceLat < -90 || geofenceLat > 90 || geofenceLng < -180 || geofenceLng > 180) {
        console.warn(`Invalid geofence coordinates: lat=${geofenceMemo.center_lat}, lng=${geofenceMemo.center_lng}`)
        return
      }
      
      const circle = L.circle([geofenceLat, geofenceLng], {
        color: '#FF0000',
        weight: 2,
        fillColor: '#FF0000',
        fillOpacity: 0.15,
        radius: geofenceMemo.radius_m || 200
      }).addTo(map)
      geofenceCircleRef.current = circle
    } else if (geofenceCircleRef.current) {
      geofenceCircleRef.current.remove()
      geofenceCircleRef.current = null
    }
    
    // Update map center to device location if coordinates exist
    // Center on the first device with valid coordinates, or use provided center
    if (mapCenter && !isNaN(mapCenter.lat) && !isNaN(mapCenter.lng)) {
      const currentCenter = map.getCenter()
      if (currentCenter) {
        const latDiff = Math.abs(currentCenter.lat - mapCenter.lat)
        const lngDiff = Math.abs(currentCenter.lng - mapCenter.lng)
        // Only update if difference is significant (more than ~100m)
        if (latDiff > 0.001 || lngDiff > 0.001) {
          console.log(`[MapView] Centering map on device:`, mapCenter)
          map.setView([mapCenter.lat, mapCenter.lng], map.getZoom())
        }
      } else {
        console.log(`[MapView] Setting initial map center:`, mapCenter)
        map.setView([mapCenter.lat, mapCenter.lng], map.getZoom())
      }
    }
    
    // If markers were created, ensure they're visible
    if (markersRef.current.length > 0) {
      console.log(`[MapView] Created ${markersRef.current.length} marker(s)`)
      // Fit map bounds to show all markers if multiple devices
      if (markersRef.current.length > 1) {
        const bounds = L.latLngBounds([])
        markersRef.current.forEach(marker => {
          bounds.extend(marker.getLatLng())
        })
        map.fitBounds(bounds, { padding: [20, 20] })
      } else if (markersRef.current.length === 1) {
        // Single marker: center on it with appropriate zoom and ensure it's visible
        const markerPos = markersRef.current[0].getLatLng()
        console.log(`[MapView] Centering map on marker at:`, markerPos)
        // Use zoom level 15 for good detail (street level)
        map.setView(markerPos, 15)
        // Open popup automatically to make marker obvious
        setTimeout(() => {
          if (markersRef.current.length > 0) {
            markersRef.current[0].openPopup()
          }
        }, 800)
      }
    } else {
      // No markers - log helpful info
      if (devices.length > 0) {
        const device = devices[0]
        const hasLat = device.last_lat !== null && device.last_lat !== undefined
        const hasLng = device.last_lng !== null && device.last_lng !== undefined
        if (!hasLat || !hasLng) {
          console.info(`[MapView] No marker: Device "${device.name}" has no location data.`, {
            last_lat: device.last_lat,
            last_lng: device.last_lng,
            suggestion: 'Ensure device agent is running and Windows Location Services is enabled'
          })
        }
      }
    }
    }
  }, [devices, mapCenter, geofenceMemo])

  // Initialize map only once
  useEffect(() => {
    const initMap = () => {
      if (!mapRef.current || initializedRef.current) return

      // Ensure map center coordinates are numbers
      const centerLat = Number(mapCenter.lat)
      const centerLng = Number(mapCenter.lng)
      const validCenter =
        !isNaN(centerLat) &&
        !isNaN(centerLng) &&
        centerLat >= -90 &&
        centerLat <= 90 &&
        centerLng >= -180 &&
        centerLng <= 180
          ? [centerLat, centerLng]
          : [3.139, 101.686] // Default to KL if invalid

      // Initialize Leaflet map
      const map = L.map(mapRef.current, {
        center: validCenter,
        zoom,
      })

      // Add OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map)

      mapInstanceRef.current = map
      initializedRef.current = true

      // Initial update of markers and geofence
      updateMapContent()
    }

    initMap()
  }, []) // Empty deps - only run once on mount

  // Update map content when data changes (but don't recreate the map)
  useEffect(() => {
    if (initializedRef.current) {
      updateMapContent()
    }
  }, [updateMapContent])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (markersRef.current.length > 0) {
        markersRef.current.forEach(marker => marker.remove())
        markersRef.current = []
      }
      if (geofenceCircleRef.current) {
        geofenceCircleRef.current.remove()
        geofenceCircleRef.current = null
      }
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  return (
    <div className="w-full h-full min-h-[500px] rounded-lg overflow-hidden shadow-lg" style={{ position: 'relative', zIndex: 1 }}>
      <div ref={mapRef} className="w-full h-full" style={{ position: 'relative', zIndex: 1 }} />
    </div>
  )
}

export default MapView
