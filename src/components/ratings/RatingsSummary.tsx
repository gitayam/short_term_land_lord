/**
 * Ratings Summary Component
 * Shows average ratings and distribution
 */

interface RatingsSummaryProps {
  averages: {
    total_ratings: number;
    avg_overall: number;
    avg_quality?: number;
    avg_timeliness?: number;
    avg_communication?: number;
    avg_professionalism?: number;
  };
  distribution: Array<{
    rating: number;
    count: number;
  }>;
}

export function RatingsSummary({ averages, distribution }: RatingsSummaryProps) {
  // Calculate percentage for each rating
  const totalRatings = averages.total_ratings || 0;
  const distributionWithPercentage = [5, 4, 3, 2, 1].map((rating) => {
    const item = distribution.find((d) => d.rating === rating);
    const count = item?.count || 0;
    const percentage = totalRatings > 0 ? (count / totalRatings) * 100 : 0;
    return { rating, count, percentage };
  });

  const StarBar = ({ rating, count, percentage }: { rating: number; count: number; percentage: number }) => (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1 w-16">
        <span className="text-sm font-medium text-gray-700">{rating}</span>
        <span className="text-yellow-500">⭐</span>
      </div>
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-yellow-500 transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
    </div>
  );

  const DetailedAverage = ({ label, value }: { label: string; value?: number }) => {
    if (!value) return null;

    return (
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">{label}</span>
        <div className="flex items-center gap-2">
          <div className="flex gap-0.5">
            {[1, 2, 3, 4, 5].map((star) => (
              <span key={star} className="text-sm">
                {star <= Math.round(value) ? '⭐' : '☆'}
              </span>
            ))}
          </div>
          <span className="text-sm font-semibold text-gray-700">{value.toFixed(1)}</span>
        </div>
      </div>
    );
  };

  if (totalRatings === 0) {
    return (
      <div className="card text-center py-8">
        <div className="text-4xl mb-2">⭐</div>
        <p className="text-gray-600">No ratings yet</p>
      </div>
    );
  }

  return (
    <div className="card">
      {/* Overall Rating */}
      <div className="flex items-center gap-6 pb-6 border-b border-gray-200">
        <div className="text-center">
          <div className="text-5xl font-bold text-gray-900 mb-1">
            {averages.avg_overall.toFixed(1)}
          </div>
          <div className="flex gap-0.5 mb-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <span key={star} className="text-2xl">
                {star <= Math.round(averages.avg_overall) ? '⭐' : '☆'}
              </span>
            ))}
          </div>
          <p className="text-sm text-gray-600">
            {totalRatings} rating{totalRatings !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Distribution Bars */}
        <div className="flex-1 space-y-2">
          {distributionWithPercentage.map((item) => (
            <StarBar
              key={item.rating}
              rating={item.rating}
              count={item.count}
              percentage={item.percentage}
            />
          ))}
        </div>
      </div>

      {/* Detailed Averages */}
      {(averages.avg_quality ||
        averages.avg_timeliness ||
        averages.avg_communication ||
        averages.avg_professionalism) && (
        <div className="pt-6 space-y-3">
          <h4 className="font-semibold text-gray-900 mb-3">Detailed Ratings</h4>
          <DetailedAverage label="Quality" value={averages.avg_quality} />
          <DetailedAverage label="Timeliness" value={averages.avg_timeliness} />
          <DetailedAverage label="Communication" value={averages.avg_communication} />
          <DetailedAverage label="Professionalism" value={averages.avg_professionalism} />
        </div>
      )}
    </div>
  );
}
