const express = require('express');
const router = express.Router();
const { check } = require('express-validator');
const propertyController = require('../controllers/propertyController');
const { authenticate, authorize } = require('../middleware/auth');
const { ROLES } = require('../models/User');

// All routes require authentication and property owner role
router.use(authenticate, authorize(ROLES.PROPERTY_OWNER));

// @route   POST /api/properties
// @desc    Create a new property
// @access  Private/Property Owner
router.post(
  '/',
  [
    check('name', 'Name is required').not().isEmpty(),
    check('address.street', 'Street address is required').not().isEmpty(),
    check('address.city', 'City is required').not().isEmpty(),
    check('address.state', 'State is required').not().isEmpty(),
    check('address.zipCode', 'Zip code is required').not().isEmpty()
  ],
  propertyController.createProperty
);

// @route   GET /api/properties
// @desc    Get all properties for the logged-in property owner
// @access  Private/Property Owner
router.get('/', propertyController.getProperties);

// @route   GET /api/properties/:id
// @desc    Get a single property by ID
// @access  Private/Property Owner
router.get('/:id', propertyController.getPropertyById);

// @route   PUT /api/properties/:id
// @desc    Update a property
// @access  Private/Property Owner
router.put(
  '/:id',
  [
    check('name', 'Name is required').optional().not().isEmpty(),
    check('address.street', 'Street address is required').optional().not().isEmpty(),
    check('address.city', 'City is required').optional().not().isEmpty(),
    check('address.state', 'State is required').optional().not().isEmpty(),
    check('address.zipCode', 'Zip code is required').optional().not().isEmpty()
  ],
  propertyController.updateProperty
);

// @route   DELETE /api/properties/:id
// @desc    Delete a property
// @access  Private/Property Owner
router.delete('/:id', propertyController.deleteProperty);

module.exports = router;
