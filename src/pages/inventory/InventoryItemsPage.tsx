import { useEffect, useState } from 'react';
import { inventoryItemsApi, propertiesApi, inventoryCatalogApi } from '../../services/api';

const CATEGORIES = [
  { value: 'linens', label: 'Linens' },
  { value: 'toiletries', label: 'Toiletries' },
  { value: 'cleaning_supplies', label: 'Cleaning Supplies' },
  { value: 'kitchen', label: 'Kitchen' },
  { value: 'appliances', label: 'Appliances' },
  { value: 'furniture', label: 'Furniture' },
  { value: 'electronics', label: 'Electronics' },
  { value: 'amenities', label: 'Amenities' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'safety', label: 'Safety' },
  { value: 'general', label: 'General' },
];

export function InventoryItemsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [properties, setProperties] = useState<any[]>([]);
  const [catalogItems, setCatalogItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    property_id: '',
    category: '',
    low_stock: false,
  });
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    property_id: '',
    catalog_item_id: '',
    name: '',
    quantity: '0',
    min_quantity: '0',
    unit: '',
    category: '',
    location: '',
    notes: '',
  });

  useEffect(() => {
    loadData();
  }, [filters]);

  const loadData = async () => {
    try {
      const [itemsData, propertiesData, catalogData] = await Promise.all([
        inventoryItemsApi.list(filters),
        propertiesApi.list(),
        inventoryCatalogApi.list(),
      ]);
      setItems(itemsData.items || []);
      setProperties(propertiesData.properties || []);
      setCatalogItems(catalogData.items || []);
    } catch (error) {
      console.error('Failed to load inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateItem = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await inventoryItemsApi.create(formData);
      setShowCreateForm(false);
      setFormData({
        property_id: '',
        catalog_item_id: '',
        name: '',
        quantity: '0',
        min_quantity: '0',
        unit: '',
        category: '',
        location: '',
        notes: '',
      });
      loadData();
    } catch (error: any) {
      alert(error.message || 'Failed to create inventory item');
    }
  };

  const handleAdjustStock = async (itemId: string, adjustment: number) => {
    try {
      await inventoryItemsApi.adjust(itemId, adjustment);
      loadData();
    } catch (error: any) {
      alert(error.message || 'Failed to adjust stock');
    }
  };

  const handleCatalogItemChange = (catalogItemId: string) => {
    const catalogItem = catalogItems.find((item) => item.id === parseInt(catalogItemId));
    if (catalogItem) {
      setFormData({
        ...formData,
        catalog_item_id: catalogItemId,
        name: catalogItem.name,
        unit: catalogItem.unit,
        category: catalogItem.category,
      });
    } else {
      setFormData({ ...formData, catalog_item_id: '' });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Property Inventory</h1>
          <p className="text-sm text-gray-600 mt-1">Track stock levels for each property</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showCreateForm ? 'Cancel' : '+ Add Inventory Item'}
        </button>
      </div>

      {showCreateForm && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Add Inventory Item</h2>
          <form onSubmit={handleCreateItem} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Property *
                </label>
                <select
                  value={formData.property_id}
                  onChange={(e) => setFormData({ ...formData, property_id: e.target.value })}
                  className="input"
                  required
                >
                  <option value="">Select property</option>
                  {properties.map((prop) => (
                    <option key={prop.id} value={prop.id}>
                      {prop.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  From Catalog (Optional)
                </label>
                <select
                  value={formData.catalog_item_id}
                  onChange={(e) => handleCatalogItemChange(e.target.value)}
                  className="input"
                >
                  <option value="">Create new item</option>
                  {catalogItems.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} ({item.category})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Item Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input"
                  placeholder="Item name"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="input"
                >
                  <option value="">Select category</option>
                  {CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Current Quantity
                </label>
                <input
                  type="number"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  className="input"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Min Quantity (Alert Level)
                </label>
                <input
                  type="number"
                  value={formData.min_quantity}
                  onChange={(e) => setFormData({ ...formData, min_quantity: e.target.value })}
                  className="input"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
                <input
                  type="text"
                  value={formData.unit}
                  onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                  className="input"
                  placeholder="e.g., each, box"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="input"
                  placeholder="e.g., Linen closet"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="input"
                rows={2}
                placeholder="Additional notes"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Add Item
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Property</label>
            <select
              value={filters.property_id}
              onChange={(e) => setFilters({ ...filters, property_id: e.target.value })}
              className="input"
            >
              <option value="">All properties</option>
              {properties.map((prop) => (
                <option key={prop.id} value={prop.id}>
                  {prop.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              value={filters.category}
              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
              className="input"
            >
              <option value="">All categories</option>
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={filters.low_stock}
                onChange={(e) => setFilters({ ...filters, low_stock: e.target.checked })}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Show low stock only</span>
            </label>
          </div>
        </div>
      </div>

      {/* Inventory List */}
      <div className="card">
        {items.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No inventory items found</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="mt-4 text-blue-600 hover:text-blue-700"
            >
              Add your first inventory item
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Item
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Property
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Category
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    Quantity
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Location
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {items.map((item) => {
                  const isLowStock = item.quantity <= item.min_quantity;
                  return (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900">{item.name}</div>
                        {item.unit && (
                          <div className="text-xs text-gray-500">Unit: {item.unit}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {item.property_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {item.category ? item.category.replace(/_/g, ' ') : '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleAdjustStock(item.id, -1)}
                            className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                            disabled={item.quantity === 0}
                          >
                            −
                          </button>
                          <span
                            className={`text-sm font-medium px-2 ${
                              isLowStock ? 'text-red-600' : 'text-gray-900'
                            }`}
                          >
                            {item.quantity}
                          </span>
                          <button
                            onClick={() => handleAdjustStock(item.id, 1)}
                            className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                          >
                            +
                          </button>
                        </div>
                        {isLowStock && (
                          <div className="text-xs text-red-600 mt-1">
                            Low stock (min: {item.min_quantity})
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {item.location || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        <button
                          onClick={async () => {
                            if (confirm('Delete this inventory item?')) {
                              await inventoryItemsApi.delete(item.id);
                              loadData();
                            }
                          }}
                          className="text-red-600 hover:text-red-700 text-sm"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
