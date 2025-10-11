/**
 * Expense Categories API
 * GET /api/expenses/categories - List all expense categories with descriptions
 */

import { Env } from '../../_middleware';

// IRS-compliant expense categories with descriptions
const EXPENSE_CATEGORIES = [
  {
    id: 'utilities',
    name: 'Utilities',
    description: 'Electricity, water, gas, internet, cable',
    tax_deductible: true,
  },
  {
    id: 'insurance',
    name: 'Insurance',
    description: 'Property, liability, business insurance',
    tax_deductible: true,
  },
  {
    id: 'property_taxes',
    name: 'Property Taxes',
    description: 'Real estate taxes',
    tax_deductible: true,
  },
  {
    id: 'mortgage_interest',
    name: 'Mortgage Interest',
    description: 'Loan interest (deductible portion)',
    tax_deductible: true,
  },
  {
    id: 'repairs_maintenance',
    name: 'Repairs & Maintenance',
    description: 'Ongoing maintenance, repairs',
    tax_deductible: true,
  },
  {
    id: 'supplies',
    name: 'Supplies',
    description: 'Cleaning supplies, amenities, consumables',
    tax_deductible: true,
  },
  {
    id: 'professional_services',
    name: 'Professional Services',
    description: 'Legal, accounting, property management',
    tax_deductible: true,
  },
  {
    id: 'marketing',
    name: 'Marketing',
    description: 'Advertising, listing fees, photography',
    tax_deductible: true,
  },
  {
    id: 'travel',
    name: 'Travel',
    description: 'Property visits, business travel',
    tax_deductible: true,
  },
  {
    id: 'depreciation',
    name: 'Depreciation',
    description: 'Asset depreciation',
    tax_deductible: true,
  },
  {
    id: 'contractor_payments',
    name: 'Contractor Payments',
    description: 'Independent contractor payments',
    tax_deductible: true,
  },
  {
    id: 'employee_wages',
    name: 'Employee Wages',
    description: 'W2 employee payments',
    tax_deductible: true,
  },
  {
    id: 'amenities',
    name: 'Amenities',
    description: 'Welcome baskets, toiletries, coffee',
    tax_deductible: true,
  },
  {
    id: 'linens_replacement',
    name: 'Linens Replacement',
    description: 'Towels, sheets, pillows',
    tax_deductible: true,
  },
  {
    id: 'furniture_replacement',
    name: 'Furniture Replacement',
    description: 'Furniture, appliances',
    tax_deductible: true,
  },
  {
    id: 'improvements',
    name: 'Improvements',
    description: 'Property improvements (capitalized)',
    tax_deductible: false, // Capitalized, not immediately deductible
  },
  {
    id: 'equipment',
    name: 'Equipment',
    description: 'Major equipment purchases',
    tax_deductible: false, // Capitalized, not immediately deductible
  },
];

// GET /api/expenses/categories
export const onRequestGet: PagesFunction<Env> = async () => {
  return new Response(
    JSON.stringify({
      success: true,
      categories: EXPENSE_CATEGORIES,
      count: EXPENSE_CATEGORIES.length,
    }),
    {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }
  );
};
