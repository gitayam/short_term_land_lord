/**
 * Reviews Display Component
 * Shows property reviews with rating breakdown and category scores
 */

import { useState } from 'react';

interface Review {
  id: number;
  guest_name: string;
  rating: number;
  title: string;
  comment: string;
  cleanliness_rating?: number;
  communication_rating?: number;
  accuracy_rating?: number;
  location_rating?: number;
  value_rating?: number;
  created_at: string;
  host_response?: string;
  host_response_date?: string;
}

interface ReviewsDisplayProps {
  propertyId: string;
  propertySlug?: string;
  propertyName: string;
  averageRating?: number;
  totalReviews?: number;
  compact?: boolean;
}

export function ReviewsDisplay({
  propertyId,
  propertySlug,
  propertyName,
  averageRating = 0,
  totalReviews = 0,
  compact = false
}: ReviewsDisplayProps) {
  const [showAllReviews, setShowAllReviews] = useState(false);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [categoryAverages, setCategoryAverages] = useState<Record<string, number>>({});
  const [ratingDistribution, setRatingDistribution] = useState<Record<number, number>>({});
  const [loading, setLoading] = useState(false);

  const loadReviews = async () => {
    if (reviews.length > 0) {
      setShowAllReviews(true);
      return;
    }

    try {
      setLoading(true);
      const slug = propertySlug || propertyId;
      const response = await fetch(`/api/reviews/${slug}`);
      const data = await response.json();

      if (response.ok) {
        setReviews(data.reviews || []);
        setCategoryAverages(data.categoryAverages || {});
        setRatingDistribution(data.ratingDistribution || {});
        setShowAllReviews(true);
      }
    } catch (error) {
      console.error('Error loading reviews:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderStars = (rating: number) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    return (
      <div className="flex items-center gap-0.5">
        {[...Array(fullStars)].map((_, i) => (
          <span key={`full-${i}`} className="text-yellow-400 text-lg">★</span>
        ))}
        {hasHalfStar && <span className="text-yellow-400 text-lg">⯪</span>}
        {[...Array(emptyStars)].map((_, i) => (
          <span key={`empty-${i}`} className="text-gray-300 text-lg">★</span>
        ))}
      </div>
    );
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'long',
      year: 'numeric'
    });
  };

  if (compact && totalReviews > 0) {
    return (
      <button
        onClick={loadReviews}
        className="flex items-center gap-2 text-sm hover:underline"
      >
        <div className="flex items-center gap-1">
          <span className="text-yellow-500 text-base">★</span>
          <span className="font-semibold">{averageRating?.toFixed(2)}</span>
        </div>
        <span className="text-gray-600">({totalReviews} {totalReviews === 1 ? 'review' : 'reviews'})</span>
      </button>
    );
  }

  if (compact && totalReviews === 0) {
    return (
      <div className="text-sm text-gray-500">
        No reviews yet
      </div>
    );
  }

  return (
    <>
      {/* Compact View (expandable) */}
      {!showAllReviews && (
        <button
          onClick={loadReviews}
          disabled={loading}
          className="w-full bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg p-4 transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-yellow-500 text-2xl">★</span>
                <span className="text-xl font-bold">{averageRating?.toFixed(2)}</span>
              </div>
              <div className="text-sm text-gray-600">
                {totalReviews} {totalReviews === 1 ? 'review' : 'reviews'}
              </div>
            </div>
            <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>
      )}

      {/* Full Reviews Modal */}
      {showAllReviews && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4" onClick={() => setShowAllReviews(false)}>
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold mb-2">Guest Reviews</h2>
                  <p className="text-yellow-100">{propertyName}</p>
                  <div className="flex items-center gap-3 mt-2">
                    <div className="flex items-center gap-2">
                      {renderStars(averageRating || 0)}
                      <span className="text-xl font-bold">{averageRating?.toFixed(2)}</span>
                    </div>
                    <span className="text-yellow-100">({totalReviews} {totalReviews === 1 ? 'review' : 'reviews'})</span>
                  </div>
                </div>
                <button
                  onClick={() => setShowAllReviews(false)}
                  className="text-white hover:text-gray-200 text-3xl font-bold"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600"></div>
                </div>
              ) : (
                <>
                  {/* Category Ratings */}
                  {Object.keys(categoryAverages).length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-5 mb-6">
                      <h3 className="font-semibold text-gray-900 mb-4">Rating Breakdown</h3>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        {Object.entries(categoryAverages).map(([category, rating]) => (
                          rating > 0 && (
                            <div key={category} className="text-center">
                              <div className="text-2xl font-bold text-gray-900">{rating.toFixed(1)}</div>
                              <div className="text-xs text-gray-600 capitalize">{category}</div>
                              {renderStars(rating)}
                            </div>
                          )
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Rating Distribution */}
                  {Object.keys(ratingDistribution).length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-5 mb-6">
                      <h3 className="font-semibold text-gray-900 mb-3">Rating Distribution</h3>
                      {[5, 4, 3, 2, 1].map((star) => {
                        const count = ratingDistribution[star] || 0;
                        const percentage = totalReviews > 0 ? (count / totalReviews) * 100 : 0;
                        return (
                          <div key={star} className="flex items-center gap-3 mb-2">
                            <span className="text-sm font-medium text-gray-700 w-8">{star} ★</span>
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-yellow-500 h-2 rounded-full"
                                style={{ width: `${percentage}%` }}
                              ></div>
                            </div>
                            <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Individual Reviews */}
                  <div className="space-y-6">
                    {reviews.length === 0 ? (
                      <p className="text-gray-500 text-center py-12">No reviews yet. Be the first to review!</p>
                    ) : (
                      reviews.map((review) => (
                        <div key={review.id} className="border-b border-gray-200 pb-6 last:border-0">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <div className="flex items-center gap-3 mb-1">
                                <span className="font-semibold text-gray-900">{review.guest_name}</span>
                                {renderStars(review.rating)}
                              </div>
                              <p className="text-xs text-gray-500">{formatDate(review.created_at)}</p>
                            </div>
                          </div>

                          {review.title && (
                            <h4 className="font-semibold text-gray-900 mb-2">{review.title}</h4>
                          )}

                          <p className="text-gray-700 whitespace-pre-wrap mb-3">{review.comment}</p>

                          {review.host_response && (
                            <div className="bg-blue-50 border-l-4 border-blue-500 rounded p-4 mt-3">
                              <p className="text-sm font-semibold text-gray-900 mb-1">Response from host:</p>
                              <p className="text-sm text-gray-700">{review.host_response}</p>
                              {review.host_response_date && (
                                <p className="text-xs text-gray-500 mt-2">{formatDate(review.host_response_date)}</p>
                              )}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </>
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-gray-200 bg-gray-50 p-4 text-center">
              <button
                onClick={() => setShowAllReviews(false)}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
