/**
 * Property Images API Service
 */

export interface PropertyImage {
  id: string;
  property_id: string;
  image_url: string;
  caption: string | null;
  display_order: number;
  is_primary: number;
  uploaded_at: string;
}

class PropertyImagesApi {
  private baseUrl = '/api';

  private getAuthToken(): string {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('Not authenticated');
    }
    return token;
  }

  async getImages(propertyId: string): Promise<PropertyImage[]> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/images`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch images');
    }

    const data = await response.json();
    return data.images;
  }

  async uploadImage(propertyId: string, file: File): Promise<PropertyImage> {
    const token = this.getAuthToken();
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/images/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to upload image');
    }

    const data = await response.json();
    return data.image;
  }

  async addImageUrl(
    propertyId: string,
    imageUrl: string,
    caption?: string
  ): Promise<PropertyImage> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/images/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_url: imageUrl,
        caption,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to add image');
    }

    const data = await response.json();
    return data.image;
  }

  async updateImage(
    propertyId: string,
    imageId: string,
    updates: {
      caption?: string;
      display_order?: number;
      is_primary?: number;
    }
  ): Promise<PropertyImage> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/images/${imageId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update image');
    }

    const data = await response.json();
    return data.image;
  }

  async deleteImage(propertyId: string, imageId: string): Promise<void> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/images/${imageId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete image');
    }
  }

  async reorderImages(
    propertyId: string,
    imageOrder: { id: string; display_order: number }[]
  ): Promise<PropertyImage[]> {
    const token = this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/images/reorder`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ image_order: imageOrder }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to reorder images');
    }

    const data = await response.json();
    return data.images;
  }
}

export const propertyImagesApi = new PropertyImagesApi();
