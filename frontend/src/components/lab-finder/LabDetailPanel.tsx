"use client";

import { X, MapPin, Phone, Globe, ExternalLink, Star } from "lucide-react";

interface LabDetailPanelProps {
  place: google.maps.places.PlaceResult;
  onClose: () => void;
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          size={12}
          className={star <= Math.round(rating) ? "fill-amber-400 text-amber-400" : "text-zinc-700"}
        />
      ))}
      <span className="text-xs text-zinc-500 ml-1">{rating.toFixed(1)}</span>
    </div>
  );
}

export function LabDetailPanel({ place, onClose }: LabDetailPanelProps) {
  return (
    <div className="w-80 shrink-0 flex flex-col bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 px-4 py-3 border-b border-zinc-800">
        <h3 className="text-sm font-semibold text-zinc-100 leading-snug">{place.name}</h3>
        <button
          onClick={onClose}
          className="shrink-0 p-1 rounded-md text-zinc-600 hover:text-zinc-300 hover:bg-zinc-800 transition-colors"
          aria-label="Close"
        >
          <X size={14} />
        </button>
      </div>

      {/* Details */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {place.rating !== undefined && (
          <StarRating rating={place.rating} />
        )}

        {place.formatted_address && (
          <div className="flex items-start gap-2">
            <MapPin size={13} className="text-zinc-500 mt-0.5 shrink-0" />
            <p className="text-xs text-zinc-400 leading-relaxed">{place.formatted_address}</p>
          </div>
        )}

        {place.formatted_phone_number && (
          <div className="flex items-center gap-2">
            <Phone size={13} className="text-zinc-500 shrink-0" />
            <a
              href={`tel:${place.formatted_phone_number}`}
              className="text-xs text-zinc-400 hover:text-indigo-400 transition-colors"
            >
              {place.formatted_phone_number}
            </a>
          </div>
        )}

        {place.website && (
          <div className="flex items-center gap-2">
            <Globe size={13} className="text-zinc-500 shrink-0" />
            <a
              href={place.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors truncate"
            >
              {new URL(place.website).hostname.replace("www.", "")}
            </a>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="px-4 py-3 border-t border-zinc-800 flex flex-col gap-2">
        {place.website && (
          <a
            href={place.website}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
          >
            <ExternalLink size={12} />
            Visit Website
          </a>
        )}
        {place.url && (
          <a
            href={place.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-medium transition-colors"
          >
            <MapPin size={12} />
            Get Directions
          </a>
        )}
      </div>
    </div>
  );
}
