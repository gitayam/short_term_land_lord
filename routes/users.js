const express = require('express');
const router = express.Router();
const { User, ROLES } = require('../models/User');
const { authenticate, authorize } = require('../middleware/auth');

// @route   GET /api/users
// @desc    Get all users (only accessible to property owners)
// @access  Private/Property Owner
router.get('/', authenticate, authorize(ROLES.PROPERTY_OWNER), async (req, res) => {
  try {
    const users = await User.find().select('-password');
    res.json(users);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
});

// @route   GET /api/users/cleaners
// @desc    Get all cleaners
// @access  Private/Property Owner
router.get('/cleaners', authenticate, authorize(ROLES.PROPERTY_OWNER), async (req, res) => {
  try {
    const cleaners = await User.find({ role: ROLES.CLEANER }).select('-password');
    res.json(cleaners);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
});

// @route   GET /api/users/maintenance
// @desc    Get all maintenance personnel
// @access  Private/Property Owner
router.get('/maintenance', authenticate, authorize(ROLES.PROPERTY_OWNER), async (req, res) => {
  try {
    const maintenance = await User.find({ role: ROLES.MAINTENANCE }).select('-password');
    res.json(maintenance);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
});

module.exports = router;
