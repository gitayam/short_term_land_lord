import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface FavoritesState {
  favorites: string[]; // Array of property slugs
  addFavorite: (slug: string) => void;
  removeFavorite: (slug: string) => void;
  toggleFavorite: (slug: string) => void;
  isFavorite: (slug: string) => boolean;
  clearFavorites: () => void;
}

export const useFavoritesStore = create<FavoritesState>()(
  persist(
    (set, get) => ({
      favorites: [],

      addFavorite: (slug: string) => {
        set((state) => ({
          favorites: [...new Set([...state.favorites, slug])]
        }));
      },

      removeFavorite: (slug: string) => {
        set((state) => ({
          favorites: state.favorites.filter((s) => s !== slug)
        }));
      },

      toggleFavorite: (slug: string) => {
        const { isFavorite, addFavorite, removeFavorite } = get();
        if (isFavorite(slug)) {
          removeFavorite(slug);
        } else {
          addFavorite(slug);
        }
      },

      isFavorite: (slug: string) => {
        return get().favorites.includes(slug);
      },

      clearFavorites: () => {
        set({ favorites: [] });
      }
    }),
    {
      name: 'openbnb-favorites', // localStorage key
    }
  )
);
