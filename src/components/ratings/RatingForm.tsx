/**
 * Rating Form Component
 * Allows users to submit ratings for staff
 */

import { useState } from 'react';

interface RatingFormProps {
  workerId: number;
  workerName: string;
  propertyId?: number;
  workLogId?: number;
  repairRequestId?: number;
  onSubmit: (rating: RatingData) => void;
  onCancel?: () => void;
}

export interface RatingData {
  worker_id: number;
  property_id?: number;
  work_log_id?: number;
  repair_request_id?: number;
  rating: number;
  quality_rating?: number;
  timeliness_rating?: number;
  communication_rating?: number;
  professionalism_rating?: number;
  comment?: string;
  is_anonymous: boolean;
}

export function RatingForm({
  workerId,
  workerName,
  propertyId,
  workLogId,
  repairRequestId,
  onSubmit,
  onCancel,
}: RatingFormProps) {
  const [rating, setRating] = useState(0);
  const [qualityRating, setQualityRating] = useState(0);
  const [timelinessRating, setTimelinessRating] = useState(0);
  const [communicationRating, setCommunicationRating] = useState(0);
  const [professionalismRating, setProfessionalismRating] = useState(0);
  const [comment, setComment] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [showDetailedRatings, setShowDetailedRatings] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (rating === 0) {
      alert('Please select an overall rating');
      return;
    }

    const ratingData: RatingData = {
      worker_id: workerId,
      property_id: propertyId,
      work_log_id: workLogId,
      repair_request_id: repairRequestId,
      rating,
      quality_rating: showDetailedRatings ? qualityRating : undefined,
      timeliness_rating: showDetailedRatings ? timelinessRating : undefined,
      communication_rating: showDetailedRatings ? communicationRating : undefined,
      professionalism_rating: showDetailedRatings ? professionalismRating : undefined,
      comment: comment.trim() || undefined,
      is_anonymous: isAnonymous,
    };

    onSubmit(ratingData);
  };

  const StarRating = ({
    value,
    onChange,
    label,
  }: {
    value: number;
    onChange: (v: number) => void;
    label: string;
  }) => (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => onChange(star)}
            className="text-2xl focus:outline-none transition-transform hover:scale-110"
          >
            {star <= value ? '⭐' : '☆'}
          </button>
        ))}
        {value > 0 && (
          <span className="ml-2 text-sm text-gray-600 self-center">{value}/5</span>
        )}
      </div>
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Rate {workerName}
        </h3>

        {/* Overall Rating */}
        <StarRating value={rating} onChange={setRating} label="Overall Rating *" />

        {/* Toggle Detailed Ratings */}
        <button
          type="button"
          onClick={() => setShowDetailedRatings(!showDetailedRatings)}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium mt-4"
        >
          {showDetailedRatings ? '− Hide' : '+ Add'} detailed ratings
        </button>

        {/* Detailed Ratings */}
        {showDetailedRatings && (
          <div className="mt-4 space-y-4 p-4 bg-gray-50 rounded-lg">
            <StarRating
              value={qualityRating}
              onChange={setQualityRating}
              label="Quality of Work"
            />
            <StarRating
              value={timelinessRating}
              onChange={setTimelinessRating}
              label="Timeliness"
            />
            <StarRating
              value={communicationRating}
              onChange={setCommunicationRating}
              label="Communication"
            />
            <StarRating
              value={professionalismRating}
              onChange={setProfessionalismRating}
              label="Professionalism"
            />
          </div>
        )}

        {/* Comment */}
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Comment (Optional)
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="Share your experience working with this staff member..."
          />
        </div>

        {/* Anonymous Option */}
        <div className="mt-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={isAnonymous}
              onChange={(e) => setIsAnonymous(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Submit anonymously</span>
          </label>
          {isAnonymous && (
            <p className="text-xs text-gray-500 mt-1 ml-6">
              Your name will not be shown to the worker
            </p>
          )}
        </div>

        {/* Buttons */}
        <div className="flex gap-3 mt-6">
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
          >
            Submit Rating
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </form>
  );
}
