"use client";

import { useState, useCallback, useEffect } from "react";
import { APIProvider, Map as GoogleMap, AdvancedMarker, useMap } from "@vis.gl/react-google-maps";
import { AlertTriangle, KeyRound } from "lucide-react";
import { ASSAY_CATEGORIES, type SearchStatus } from "./types";
import { AssayFilterPanel } from "./AssayFilterPanel";
import { MapSearchControls } from "./MapSearchControls";
import { LabDetailPanel } from "./LabDetailPanel";

// Inner component — must be rendered inside <APIProvider> to use useMap()
function LabFinderInner() {
  const map = useMap();

  const [userLocation, setUserLocation] = useState<google.maps.LatLngLiteral | null>(null);
  const [selectedAssayIds, setSelectedAssayIds] = useState<Set<string>>(
    new Set(["flow_cytometry", "elisa", "genomics"])
  );
  const [radius, setRadius] = useState(5000);
  const [places, setPlaces] = useState<google.maps.places.PlaceResult[]>([]);
  const [selectedPlace, setSelectedPlace] = useState<google.maps.places.PlaceResult | null>(null);
  const [searchStatus, setSearchStatus] = useState<SearchStatus>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const runSearch = useCallback(
    (location: google.maps.LatLngLiteral) => {
      if (!map) return;

      const keywords = ASSAY_CATEGORIES
        .filter((c) => selectedAssayIds.has(c.id))
        .flatMap((c) => c.keywords);

      if (keywords.length === 0) return;

      setSearchStatus("searching");
      setSelectedPlace(null);

      const service = new google.maps.places.PlacesService(map);
      const allResults = new Map<string, google.maps.places.PlaceResult>();
      let pending = keywords.length;

      keywords.forEach((keyword) => {
        service.nearbySearch(
          { location, radius, keyword, type: "establishment" },
          (results, status) => {
            pending--;
            if (status === google.maps.places.PlacesServiceStatus.OK && results) {
              results.forEach((r) => {
                if (r.place_id) allResults.set(r.place_id, r);
              });
            }
            if (pending === 0) {
              setPlaces(Array.from(allResults.values()));
              setSearchStatus(allResults.size > 0 ? "results" : "empty");
            }
          }
        );
      });
    },
    [map, selectedAssayIds, radius]
  );

  // Re-run search when filters or radius change (only if location is already known)
  useEffect(() => {
    if (userLocation) runSearch(userLocation);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAssayIds, radius]);

  const handleSearchNearMe = () => {
    if (!navigator.geolocation) {
      setSearchStatus("error");
      setErrorMessage("Geolocation is not supported by your browser.");
      return;
    }
    setSearchStatus("locating");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setUserLocation(loc);
        runSearch(loc);
      },
      () => {
        setSearchStatus("error");
        setErrorMessage("Location access was denied. Please allow location access and try again.");
      },
      { timeout: 10_000, maximumAge: 60_000 }
    );
  };

  const handleMarkerClick = (placeId: string) => {
    if (!map) return;
    const service = new google.maps.places.PlacesService(map);
    service.getDetails(
      {
        placeId,
        fields: [
          "name",
          "formatted_address",
          "formatted_phone_number",
          "rating",
          "website",
          "url",
          "geometry",
        ],
      },
      (result, status) => {
        if (status === google.maps.places.PlacesServiceStatus.OK && result) {
          setSelectedPlace(result);
        }
      }
    );
  };

  const toggleAssay = (id: string) => {
    setSelectedAssayIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const searchDisabled = selectedAssayIds.size === 0 || searchStatus === "locating" || searchStatus === "searching";

  return (
    <div className="flex gap-4 h-[calc(100vh-10rem)]">
      {/* Left: assay filter panel */}
      <AssayFilterPanel
        categories={ASSAY_CATEGORIES}
        selectedIds={selectedAssayIds}
        onToggle={toggleAssay}
      />

      {/* Center: map */}
      <div className="flex-1 relative rounded-xl overflow-hidden border border-zinc-800">
        <MapSearchControls
          status={searchStatus}
          radius={radius}
          onRadiusChange={(r: number) => setRadius(r)}
          onSearch={handleSearchNearMe}
          resultCount={places.length}
          disabled={searchDisabled}
        />

        {searchStatus === "error" && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400 shadow-lg backdrop-blur">
            <AlertTriangle size={13} />
            {errorMessage}
          </div>
        )}

        <GoogleMap
          defaultZoom={2}
          defaultCenter={{ lat: 20, lng: 0 }}
          {...(userLocation ? { center: userLocation, zoom: 12 } : {})}
          colorScheme="DARK"
          gestureHandling="greedy"
          disableDefaultUI={false}
          style={{ width: "100%", height: "100%" }}
        >
          {/* User location marker */}
          {userLocation && (
            <AdvancedMarker position={userLocation} title="Your location">
              <div className="w-4 h-4 rounded-full bg-blue-500 border-2 border-white shadow-lg" />
            </AdvancedMarker>
          )}

          {/* Lab markers */}
          {places.map((place) =>
            place.geometry?.location ? (
              <AdvancedMarker
                key={place.place_id}
                position={{
                  lat: place.geometry.location.lat(),
                  lng: place.geometry.location.lng(),
                }}
                title={place.name}
                onClick={() => handleMarkerClick(place.place_id!)}
              >
                <div
                  className="w-7 h-7 rounded-full bg-indigo-600 border-2 border-white shadow-lg flex items-center justify-center cursor-pointer hover:bg-indigo-500 transition-colors"
                  title={place.name}
                >
                  <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-white">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                  </svg>
                </div>
              </AdvancedMarker>
            ) : null
          )}
        </GoogleMap>
      </div>

      {/* Right: lab detail panel */}
      {selectedPlace && (
        <LabDetailPanel place={selectedPlace} onClose={() => setSelectedPlace(null)} />
      )}
    </div>
  );
}

function NoApiKeyBanner() {
  return (
    <div className="flex flex-col items-center justify-center h-96 gap-4 text-center">
      <div className="w-14 h-14 rounded-2xl bg-amber-500/10 flex items-center justify-center">
        <KeyRound size={24} className="text-amber-400" />
      </div>
      <div className="space-y-1">
        <p className="text-zinc-300 font-medium text-sm">Google Maps API key required</p>
        <p className="text-zinc-500 text-xs max-w-sm leading-relaxed">
          Add <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-300 font-mono">NEXT_PUBLIC_GOOGLE_MAPS_API_KEY</code> to{" "}
          <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-300 font-mono">.env.local</code> and restart the dev server.
        </p>
        <p className="text-zinc-600 text-xs mt-2">
          Enable: Maps JavaScript API + Places API in Google Cloud Console.
        </p>
      </div>
    </div>
  );
}

export function LabFinderClient() {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";

  if (!apiKey) {
    return <NoApiKeyBanner />;
  }

  return (
    <APIProvider apiKey={apiKey} libraries={["places"]}>
      <LabFinderInner />
    </APIProvider>
  );
}
