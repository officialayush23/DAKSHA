// LocationInput.jsx (or keep it in same file ABOVE CreateLocation)

import React, { useState } from "react";

export function LocationInput({ onDetect }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleDetectLocation = () => {
    setLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        onDetect({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setLoading(false);
      },
      () => {
        setError("Unable to retrieve location. Allow location access.");
        setLoading(false);
      }
    );
  };

  return (
    <div className="space-y-3 p-4 rounded-xl bg-zinc-900 border border-zinc-800">
      <button
        type="button"
        onClick={handleDetectLocation}
        disabled={loading}
        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 rounded-lg"
      >
        {loading ? "Detecting..." : " Detect My Location"}
      </button>

      {error && <p className="text-red-500 text-xs">{error}</p>}
    </div>
  );
}
