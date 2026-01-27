import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const LocationPicker = ({ onLocationSelect, initialLocation }) => {
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const mapInstanceRef = useRef(null)

  useEffect(() => {
    const initMap = () => {
      if (!mapRef.current) return
      
      // Initialize map with initial location or default (Kuala Lumpur)
      const center = initialLocation || { lat: 3.139, lng: 101.686 }

      const map = L.map(mapRef.current, {
        center: [center.lat, center.lng],
        zoom: 15,
      })

      // OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map)

      // Draggable marker
      const marker = L.marker([center.lat, center.lng], {
        draggable: true,
        title: 'Drag to set device location',
      }).addTo(map)

      markerRef.current = marker
      mapInstanceRef.current = map

      // Update location when marker is dragged
      marker.on('dragend', () => {
        const position = marker.getLatLng()
        onLocationSelect({
          lat: position.lat,
          lng: position.lng,
        })
      })

      // Update location when map is clicked
      map.on('click', (e) => {
        const { lat, lng } = e.latlng
        marker.setLatLng([lat, lng])
        onLocationSelect({ lat, lng })
      })
    }

    initMap()
  }, [initialLocation, onLocationSelect])

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          }
          
          if (markerRef.current && mapInstanceRef.current) {
            markerRef.current.setLatLng([location.lat, location.lng])
            mapInstanceRef.current.setView([location.lat, location.lng], 17)
          }
          
          onLocationSelect(location)
        },
        (error) => {
          alert('Error getting your location: ' + error.message)
        }
      )
    } else {
      alert('Geolocation is not supported by your browser')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Select Device Location</h3>
        <button
          onClick={getCurrentLocation}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm"
        >
          📍 Use My Current Location
        </button>
      </div>
      <div className="w-full h-96 rounded-lg overflow-hidden border border-gray-300">
        <div ref={mapRef} className="w-full h-full" />
      </div>
      <p className="text-sm text-gray-600">
        Click on the map or drag the marker to set the exact location
      </p>
    </div>
  )
}

export default LocationPicker

