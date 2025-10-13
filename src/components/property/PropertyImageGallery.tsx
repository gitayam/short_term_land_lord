/**
 * Property Image Gallery Component
 * Manage property images - upload, reorder, caption, delete
 */

import { useState, useEffect, useRef } from 'react';
import { propertyImagesApi, PropertyImage } from '../../services/propertyImagesApi';

interface PropertyImageGalleryProps {
  propertyId: string;
}

export function PropertyImageGallery({ propertyId }: PropertyImageGalleryProps) {
  const [images, setImages] = useState<PropertyImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [editingCaption, setEditingCaption] = useState<string | null>(null);
  const [captionValue, setCaptionValue] = useState('');

  const [showUrlInput, setShowUrlInput] = useState(false);
  const [imageUrl, setImageUrl] = useState('');
  const [urlCaption, setUrlCaption] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadImages();
  }, [propertyId]);

  const loadImages = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await propertyImagesApi.getImages(propertyId);
      setImages(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (files: FileList) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      // Upload files one by one
      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        // Validate file type
        if (!file.type.startsWith('image/')) {
          throw new Error(`${file.name} is not an image file`);
        }

        // Validate file size (10MB max)
        if (file.size > 10 * 1024 * 1024) {
          throw new Error(`${file.name} is too large (max 10MB)`);
        }

        await propertyImagesApi.uploadImage(propertyId, file);
      }

      await loadImages();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFileSelect(e.target.files);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.dataTransfer.files) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleAddUrl = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!imageUrl.trim()) return;

    try {
      setUploading(true);
      setError(null);
      await propertyImagesApi.addImageUrl(propertyId, imageUrl, urlCaption || undefined);
      setImageUrl('');
      setUrlCaption('');
      setShowUrlInput(false);
      await loadImages();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleSetPrimary = async (imageId: string) => {
    try {
      setError(null);
      await propertyImagesApi.updateImage(propertyId, imageId, { is_primary: 1 });
      await loadImages();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleUpdateCaption = async (imageId: string) => {
    try {
      setError(null);
      await propertyImagesApi.updateImage(propertyId, imageId, { caption: captionValue });
      setEditingCaption(null);
      setCaptionValue('');
      await loadImages();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteImage = async (imageId: string) => {
    if (!confirm('Are you sure you want to delete this image?')) return;

    try {
      setError(null);
      await propertyImagesApi.deleteImage(propertyId, imageId);
      await loadImages();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const handleDragOverImage = (e: React.DragEvent, index: number) => {
    e.preventDefault();

    if (draggedIndex === null || draggedIndex === index) return;

    // Reorder array
    const newImages = [...images];
    const draggedImage = newImages[draggedIndex];
    newImages.splice(draggedIndex, 1);
    newImages.splice(index, 0, draggedImage);

    setImages(newImages);
    setDraggedIndex(index);
  };

  const handleDropImage = async (e: React.DragEvent) => {
    e.preventDefault();

    if (draggedIndex === null) return;

    try {
      setError(null);

      // Update display order for all images
      const imageOrder = images.map((img, idx) => ({
        id: img.id,
        display_order: idx + 1,
      }));

      await propertyImagesApi.reorderImages(propertyId, imageOrder);
      await loadImages();
    } catch (err: any) {
      setError(err.message);
      await loadImages(); // Reload to reset order on error
    } finally {
      setDraggedIndex(null);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <p className="mt-2 text-gray-600">Loading images...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Property Images</h2>
          <p className="text-sm text-gray-600 mt-1">
            Upload and manage photos for your property ({images.length} images)
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <h3 className="font-semibold text-lg mb-3">Add Images</h3>

        {/* Upload Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {uploading ? 'Uploading...' : '📁 Choose Files'}
          </button>

          <button
            onClick={() => setShowUrlInput(!showUrlInput)}
            disabled={uploading}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
          >
            🔗 Add URL
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileInputChange}
          className="hidden"
        />

        {/* Drag & Drop Zone */}
        <div
          ref={dropZoneRef}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors"
        >
          <div className="text-gray-600">
            <p className="text-lg font-medium mb-2">📸 Drag & Drop Images Here</p>
            <p className="text-sm">or click "Choose Files" above</p>
            <p className="text-xs mt-2 text-gray-500">Supports JPG, PNG, WEBP (max 10MB each)</p>
          </div>
        </div>

        {/* URL Input */}
        {showUrlInput && (
          <form onSubmit={handleAddUrl} className="border border-gray-300 rounded-lg p-4 space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Image URL *
              </label>
              <input
                type="url"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="https://example.com/image.jpg"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Caption (optional)
              </label>
              <input
                type="text"
                value={urlCaption}
                onChange={(e) => setUrlCaption(e.target.value)}
                placeholder="Living room with fireplace"
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setShowUrlInput(false);
                  setImageUrl('');
                  setUrlCaption('');
                }}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={uploading}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {uploading ? 'Adding...' : 'Add Image'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Images Grid */}
      {images.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <p className="text-gray-600 text-lg">No images yet</p>
          <p className="text-gray-500 text-sm mt-2">Add photos to showcase your property</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-4">
            <h3 className="font-semibold text-lg">Image Gallery</h3>
            <p className="text-sm text-gray-600">Drag images to reorder • Click star to set as primary</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {images.map((image, index) => (
              <div
                key={image.id}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragEnd={handleDragEnd}
                onDragOver={(e) => handleDragOverImage(e, index)}
                onDrop={handleDropImage}
                className={`relative group border-2 rounded-lg overflow-hidden cursor-move transition-all ${
                  draggedIndex === index ? 'opacity-50 scale-95' : ''
                } ${image.is_primary === 1 ? 'border-yellow-400' : 'border-gray-200 hover:border-blue-400'}`}
              >
                {/* Image */}
                <div className="aspect-square bg-gray-100">
                  <img
                    src={image.image_url}
                    alt={image.caption || `Property image ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* Primary Badge */}
                {image.is_primary === 1 && (
                  <div className="absolute top-2 left-2 bg-yellow-400 text-yellow-900 px-2 py-1 rounded text-xs font-bold">
                    ⭐ PRIMARY
                  </div>
                )}

                {/* Order Badge */}
                <div className="absolute top-2 right-2 bg-gray-800 bg-opacity-75 text-white px-2 py-1 rounded text-xs font-medium">
                  #{index + 1}
                </div>

                {/* Actions Overlay */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity">
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex gap-2">
                      {image.is_primary !== 1 && (
                        <button
                          onClick={() => handleSetPrimary(image.id)}
                          title="Set as primary"
                          className="p-2 bg-yellow-400 text-yellow-900 rounded hover:bg-yellow-500"
                        >
                          ⭐
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setEditingCaption(image.id);
                          setCaptionValue(image.caption || '');
                        }}
                        title="Edit caption"
                        className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDeleteImage(image.id)}
                        title="Delete image"
                        className="p-2 bg-red-500 text-white rounded hover:bg-red-600"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>

                {/* Caption */}
                {image.caption && editingCaption !== image.id && (
                  <div className="absolute bottom-0 left-0 right-0 bg-gray-900 bg-opacity-75 text-white text-xs p-2">
                    {image.caption}
                  </div>
                )}

                {/* Edit Caption */}
                {editingCaption === image.id && (
                  <div className="absolute bottom-0 left-0 right-0 bg-white p-2 shadow-lg">
                    <input
                      type="text"
                      value={captionValue}
                      onChange={(e) => setCaptionValue(e.target.value)}
                      placeholder="Add caption..."
                      className="w-full px-2 py-1 text-xs border border-gray-300 rounded mb-1"
                      autoFocus
                    />
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleUpdateCaption(image.id)}
                        className="flex-1 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setEditingCaption(null);
                          setCaptionValue('');
                        }}
                        className="flex-1 px-2 py-1 text-xs bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">📸 Photo Tips</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Upload 10-20 high-quality photos for best results</li>
          <li>• Set a primary image - it will be the first thing guests see</li>
          <li>• Include photos of each room, amenities, and outdoor spaces</li>
          <li>• Use captions to describe special features</li>
          <li>• Drag and drop to reorder images</li>
        </ul>
      </div>
    </div>
  );
}
