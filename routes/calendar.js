const express = require('express');
const router = express.Router();
const { check } = require('express-validator');
const calendarController = require('../controllers/calendarController');
const { authenticate, authorize } = require('../middleware/auth');
const { ROLES } = require('../models/User');

// All routes require authentication and property owner role
router.use(authenticate, authorize(ROLES.PROPERTY_OWNER));

// @route   POST /api/calendar/import
// @desc    Import calendar data and create reservations
// @access  Private/Property Owner
router.post(
  '/import',
  [
    check('propertyId', 'Property ID is required').not().isEmpty(),
    check('reservations', 'Reservations array is required').isArray(),
    check('reservations.*.checkInDate', 'Check-in date is required for all reservations').exists(),
    check('reservations.*.checkOutDate', 'Check-out date is required for all reservations').exists(),
    check('reservations.*.guestName', 'Guest name is required for all reservations').not().isEmpty(),
    check('source', 'Source is required').isIn(['airbnb', 'zillow', 'manual', 'other'])
  ],
  calendarController.importCalendarData
);

// @route   GET /api/calendar/reservations/:propertyId
// @desc    Get all reservations for a property
// @access  Private/Property Owner
router.get('/reservations/:propertyId', calendarController.getReservations);

module.exports = router;
