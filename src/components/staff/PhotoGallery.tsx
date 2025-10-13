/**
 * Photo Gallery Component
 * Displays before/after comparison views for staff work logs
 */

import { useState } from 'react';

export interface WorkPhoto {
  url: string;
  type: 'before' | 'after' | 'progress';
  caption?: string;
  timestamp: string;
}

interface PhotoGalleryProps {
  photos: WorkPhoto[];
  showComparison?: boolean;
}

export function PhotoGallery({ photos, showComparison = true }: PhotoGalleryProps) {
  const [selectedPhoto, setSelectedPhoto] = useState<WorkPhoto | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'comparison'>('grid');

  const beforePhotos = photos.filter((p) => p.type === 'before');
  const afterPhotos = photos.filter((p) => p.type === 'after');
  const progressPhotos = photos.filter((p) => p.type === 'progress');

  const hasBeforeAfter = beforePhotos.length > 0 && afterPhotos.length > 0;

  return (
    <div className="space-y-4">
      {/* View Mode Toggle */}
      {hasBeforeAfter && showComparison && (
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              viewMode === 'grid'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Grid View
          </button>
          <button
            onClick={() => setViewMode('comparison')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              viewMode === 'comparison'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Before/After
          </button>
        </div>
      )}

      {/* Comparison View */}
      {viewMode === 'comparison' && hasBeforeAfter && (
        <div className="space-y-6">
          {beforePhotos.map((beforePhoto, idx) => {
            const afterPhoto = afterPhotos[idx] || afterPhotos[0];
            return (
              <div key={idx} className="card">
                <h3 className="font-semibold text-gray-900 mb-3">
                  Comparison {idx + 1}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Before */}
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded">
                        BEFORE
                      </span>
                      {beforePhoto.caption && (
                        <span className="text-sm text-gray-600">{beforePhoto.caption}</span>
                      )}
                    </div>
                    <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
                      <img
                        src={beforePhoto.url}
                        alt="Before"
                        className="w-full h-full object-cover cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => setSelectedPhoto(beforePhoto)}
                      />
                    </div>
                  </div>

                  {/* After */}
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                        AFTER
                      </span>
                      {afterPhoto.caption && (
                        <span className="text-sm text-gray-600">{afterPhoto.caption}</span>
                      )}
                    </div>
                    <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
                      <img
                        src={afterPhoto.url}
                        alt="After"
                        className="w-full h-full object-cover cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => setSelectedPhoto(afterPhoto)}
                      />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Grid View */}
      {viewMode === 'grid' && (
        <div className="space-y-4">
          {/* Before Photos */}
          {beforePhotos.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded">
                  BEFORE
                </span>
                <span className="text-sm text-gray-600">({beforePhotos.length} photos)</span>
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {beforePhotos.map((photo, idx) => (
                  <div
                    key={idx}
                    className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
                    onClick={() => setSelectedPhoto(photo)}
                  >
                    <img
                      src={photo.url}
                      alt={`Before ${idx + 1}`}
                      className="w-full h-full object-cover"
                    />
                    {photo.caption && (
                      <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white text-xs p-2">
                        {photo.caption}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Progress Photos */}
          {progressPhotos.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                  IN PROGRESS
                </span>
                <span className="text-sm text-gray-600">({progressPhotos.length} photos)</span>
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {progressPhotos.map((photo, idx) => (
                  <div
                    key={idx}
                    className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
                    onClick={() => setSelectedPhoto(photo)}
                  >
                    <img
                      src={photo.url}
                      alt={`Progress ${idx + 1}`}
                      className="w-full h-full object-cover"
                    />
                    {photo.caption && (
                      <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white text-xs p-2">
                        {photo.caption}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* After Photos */}
          {afterPhotos.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                  AFTER
                </span>
                <span className="text-sm text-gray-600">({afterPhotos.length} photos)</span>
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {afterPhotos.map((photo, idx) => (
                  <div
                    key={idx}
                    className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
                    onClick={() => setSelectedPhoto(photo)}
                  >
                    <img
                      src={photo.url}
                      alt={`After ${idx + 1}`}
                      className="w-full h-full object-cover"
                    />
                    {photo.caption && (
                      <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white text-xs p-2">
                        {photo.caption}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {photos.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <div className="text-4xl mb-2">📷</div>
          <p className="text-gray-600">No photos uploaded yet</p>
        </div>
      )}

      {/* Lightbox Modal */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedPhoto(null)}
        >
          <div className="relative max-w-4xl w-full">
            <button
              onClick={() => setSelectedPhoto(null)}
              className="absolute top-4 right-4 text-white text-3xl hover:text-gray-300"
            >
              ×
            </button>
            <img
              src={selectedPhoto.url}
              alt="Full size"
              className="w-full h-auto rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
            {selectedPhoto.caption && (
              <div className="mt-4 text-white text-center">
                <p className="text-lg">{selectedPhoto.caption}</p>
                <p className="text-sm text-gray-400 mt-1">
                  {new Date(selectedPhoto.timestamp).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
