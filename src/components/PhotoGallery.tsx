/**
 * Photo Gallery Component
 * Displays property images in a carousel with full-screen modal view
 */

import { useState } from 'react';

interface PropertyImage {
  id: number;
  image_url: string;
  caption?: string;
  display_order: number;
  is_primary: boolean;
}

interface PhotoGalleryProps {
  images: PropertyImage[];
  propertyName: string;
}

export function PhotoGallery({ images, propertyName }: PhotoGalleryProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!images || images.length === 0) {
    return null;
  }

  const openModal = (index: number) => {
    setCurrentIndex(index);
    setIsModalOpen(true);
    document.body.style.overflow = 'hidden';
  };

  const closeModal = () => {
    setIsModalOpen(false);
    document.body.style.overflow = 'auto';
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev + 1) % images.length);
  };

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') closeModal();
    if (e.key === 'ArrowRight') goToNext();
    if (e.key === 'ArrowLeft') goToPrevious();
  };

  return (
    <>
      {/* Thumbnail Grid */}
      <div className="grid grid-cols-4 gap-2">
        {images.slice(0, 4).map((image, index) => (
          <div
            key={image.id}
            className="relative aspect-square cursor-pointer rounded-lg overflow-hidden group"
            onClick={() => openModal(index)}
          >
            <img
              src={image.image_url}
              alt={image.caption || `${propertyName} - Photo ${index + 1}`}
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
            />
            {/* Overlay on hover */}
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity duration-300"></div>

            {/* "View all photos" overlay for last image if more than 4 */}
            {index === 3 && images.length > 4 && (
              <div className="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center text-white font-semibold text-sm">
                +{images.length - 4} photos
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Full-Screen Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 bg-black bg-opacity-95 flex items-center justify-center"
          onClick={closeModal}
          onKeyDown={handleKeyDown}
          tabIndex={0}
        >
          {/* Close Button */}
          <button
            onClick={closeModal}
            className="absolute top-4 right-4 text-white hover:text-gray-300 text-4xl font-bold z-10"
            aria-label="Close gallery"
          >
            ×
          </button>

          {/* Previous Button */}
          {images.length > 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                goToPrevious();
              }}
              className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white hover:text-gray-300 text-5xl font-bold z-10"
              aria-label="Previous image"
            >
              ‹
            </button>
          )}

          {/* Image */}
          <div
            className="max-w-6xl max-h-[90vh] w-full px-16"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={images[currentIndex].image_url}
              alt={images[currentIndex].caption || `${propertyName} - Photo ${currentIndex + 1}`}
              className="w-full h-full object-contain"
            />
            {/* Caption */}
            {images[currentIndex].caption && (
              <p className="text-center text-white mt-4 text-sm">
                {images[currentIndex].caption}
              </p>
            )}
            {/* Counter */}
            <p className="text-center text-gray-400 mt-2 text-xs">
              {currentIndex + 1} / {images.length}
            </p>
          </div>

          {/* Next Button */}
          {images.length > 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                goToNext();
              }}
              className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white hover:text-gray-300 text-5xl font-bold z-10"
              aria-label="Next image"
            >
              ›
            </button>
          )}

          {/* Thumbnail Navigation */}
          <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2 overflow-x-auto max-w-xl">
            {images.map((image, index) => (
              <button
                key={image.id}
                onClick={(e) => {
                  e.stopPropagation();
                  setCurrentIndex(index);
                }}
                className={`flex-shrink-0 w-16 h-16 rounded-md overflow-hidden border-2 transition-all ${
                  index === currentIndex
                    ? 'border-white scale-110'
                    : 'border-transparent opacity-60 hover:opacity-100'
                }`}
              >
                <img
                  src={image.image_url}
                  alt={`Thumbnail ${index + 1}`}
                  className="w-full h-full object-cover"
                />
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
