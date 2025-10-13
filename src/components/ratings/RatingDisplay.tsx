/**
 * Rating Display Component
 * Shows individual ratings with details
 */

import { useState } from 'react';

interface Rating {
  id: number;
  rating: number;
  quality_rating?: number;
  timeliness_rating?: number;
  communication_rating?: number;
  professionalism_rating?: number;
  comment?: string;
  is_anonymous: number;
  rated_by_name?: string;
  property_name?: string;
  repair_title?: string;
  created_at: string;
  response?: {
    response_text: string;
    created_at: string;
  };
}

interface RatingDisplayProps {
  ratings: Rating[];
  canRespond?: boolean;
  onRespond?: (ratingId: number, response: string) => void;
}

export function RatingDisplay({ ratings, canRespond, onRespond }: RatingDisplayProps) {
  const [respondingTo, setRespondingTo] = useState<number | null>(null);
  const [responseText, setResponseText] = useState('');

  const handleSubmitResponse = (ratingId: number) => {
    if (!responseText.trim()) {
      alert('Please enter a response');
      return;
    }

    if (onRespond) {
      onRespond(ratingId, responseText);
      setRespondingTo(null);
      setResponseText('');
    }
  };

  const StarDisplay = ({ value, label }: { value?: number; label: string }) => {
    if (!value) return null;

    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-600">{label}:</span>
        <div className="flex gap-0.5">
          {[1, 2, 3, 4, 5].map((star) => (
            <span key={star} className="text-sm">
              {star <= value ? '⭐' : '☆'}
            </span>
          ))}
        </div>
        <span className="text-xs text-gray-500">{value}/5</span>
      </div>
    );
  };

  if (ratings.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <div className="text-4xl mb-2">⭐</div>
        <p className="text-gray-600">No ratings yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {ratings.map((rating) => (
        <div key={rating.id} className="card">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                {/* Overall Rating Stars */}
                <div className="flex gap-0.5">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <span key={star} className="text-xl">
                      {star <= rating.rating ? '⭐' : '☆'}
                    </span>
                  ))}
                </div>
                <span className="text-sm font-semibold text-gray-700">
                  {rating.rating}/5
                </span>
              </div>

              <div className="text-sm text-gray-600">
                by {rating.is_anonymous ? 'Anonymous' : rating.rated_by_name}
                {rating.property_name && (
                  <span className="text-gray-400"> • {rating.property_name}</span>
                )}
                {rating.repair_title && (
                  <span className="text-gray-400"> • {rating.repair_title}</span>
                )}
              </div>
            </div>

            <div className="text-xs text-gray-500">
              {new Date(rating.created_at).toLocaleDateString()}
            </div>
          </div>

          {/* Detailed Ratings */}
          {(rating.quality_rating ||
            rating.timeliness_rating ||
            rating.communication_rating ||
            rating.professionalism_rating) && (
            <div className="space-y-1 mb-3 p-3 bg-gray-50 rounded-lg">
              <StarDisplay value={rating.quality_rating} label="Quality" />
              <StarDisplay value={rating.timeliness_rating} label="Timeliness" />
              <StarDisplay value={rating.communication_rating} label="Communication" />
              <StarDisplay value={rating.professionalism_rating} label="Professionalism" />
            </div>
          )}

          {/* Comment */}
          {rating.comment && (
            <p className="text-gray-700 mb-3 leading-relaxed">{rating.comment}</p>
          )}

          {/* Response */}
          {rating.response && (
            <div className="mt-3 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
              <div className="flex items-start gap-2">
                <span className="text-blue-600 font-semibold text-sm">Response:</span>
                <div className="flex-1">
                  <p className="text-gray-700 text-sm">{rating.response.response_text}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(rating.response.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Respond Button */}
          {canRespond && !rating.response && (
            <div className="mt-3">
              {respondingTo === rating.id ? (
                <div className="space-y-2">
                  <textarea
                    value={responseText}
                    onChange={(e) => setResponseText(e.target.value)}
                    rows={3}
                    placeholder="Write your response..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSubmitResponse(rating.id)}
                      className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 font-medium"
                    >
                      Submit Response
                    </button>
                    <button
                      onClick={() => {
                        setRespondingTo(null);
                        setResponseText('');
                      }}
                      className="px-3 py-1.5 text-gray-600 text-sm rounded hover:text-gray-800"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setRespondingTo(rating.id)}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Respond
                </button>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
