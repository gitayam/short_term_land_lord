/**
 * Photo Upload Component
 * Allows staff to upload categorized photos (before/after/progress) with captions
 */

import { useState, useRef } from 'react';
import { WorkPhoto } from './PhotoGallery';

interface PhotoUploadProps {
  onPhotosAdded: (photos: WorkPhoto[]) => void;
  maxPhotos?: number;
}

export function PhotoUpload({ onPhotosAdded, maxPhotos = 10 }: PhotoUploadProps) {
  const [photos, setPhotos] = useState<WorkPhoto[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    if (photos.length + files.length > maxPhotos) {
      alert(`Maximum ${maxPhotos} photos allowed`);
      return;
    }

    setUploading(true);

    try {
      // Upload each file to R2 via API
      const uploadPromises = files.map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', 'work-photos');

        const token = localStorage.getItem('auth_token');
        const response = await fetch('/api/upload/image', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const data = await response.json();

        return {
          url: data.url,
          type: 'progress' as const,
          caption: '',
          timestamp: new Date().toISOString(),
        };
      });

      const uploadedPhotos = await Promise.all(uploadPromises);
      setPhotos([...photos, ...uploadedPhotos]);
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload photos. Please try again.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const updatePhoto = (index: number, updates: Partial<WorkPhoto>) => {
    const updated = [...photos];
    updated[index] = { ...updated[index], ...updates };
    setPhotos(updated);
  };

  const removePhoto = (index: number) => {
    setPhotos(photos.filter((_, i) => i !== index));
  };

  const handleDone = () => {
    onPhotosAdded(photos);
  };

  return (
    <div className="space-y-4">
      {/* Upload Button */}
      <div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          disabled={uploading || photos.length >= maxPhotos}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading || photos.length >= maxPhotos}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {uploading ? (
            <div className="flex items-center justify-center gap-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Uploading...</span>
            </div>
          ) : (
            `📷 Add Photos (${photos.length}/${maxPhotos})`
          )}
        </button>
      </div>

      {/* Photo List */}
      {photos.length > 0 && (
        <div className="space-y-3">
          {photos.map((photo, idx) => (
            <div key={idx} className="card">
              <div className="flex gap-3">
                {/* Thumbnail */}
                <div className="flex-shrink-0 w-24 h-24 bg-gray-100 rounded-lg overflow-hidden">
                  <img src={photo.url} alt={`Photo ${idx + 1}`} className="w-full h-full object-cover" />
                </div>

                {/* Details */}
                <div className="flex-1 space-y-2">
                  {/* Type Selection */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Photo Type
                    </label>
                    <div className="flex gap-2">
                      <button
                        onClick={() => updatePhoto(idx, { type: 'before' })}
                        className={`px-3 py-1 text-xs font-medium rounded ${
                          photo.type === 'before'
                            ? 'bg-orange-100 text-orange-800 border border-orange-300'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        Before
                      </button>
                      <button
                        onClick={() => updatePhoto(idx, { type: 'progress' })}
                        className={`px-3 py-1 text-xs font-medium rounded ${
                          photo.type === 'progress'
                            ? 'bg-blue-100 text-blue-800 border border-blue-300'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        Progress
                      </button>
                      <button
                        onClick={() => updatePhoto(idx, { type: 'after' })}
                        className={`px-3 py-1 text-xs font-medium rounded ${
                          photo.type === 'after'
                            ? 'bg-green-100 text-green-800 border border-green-300'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        After
                      </button>
                    </div>
                  </div>

                  {/* Caption */}
                  <div>
                    <input
                      type="text"
                      placeholder="Add caption (optional)"
                      value={photo.caption || ''}
                      onChange={(e) => updatePhoto(idx, { caption: e.target.value })}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => removePhoto(idx)}
                  className="flex-shrink-0 text-red-600 hover:text-red-700 text-xl"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Done Button */}
      {photos.length > 0 && (
        <button
          onClick={handleDone}
          className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
        >
          ✓ Done ({photos.length} photo{photos.length !== 1 ? 's' : ''})
        </button>
      )}
    </div>
  );
}
