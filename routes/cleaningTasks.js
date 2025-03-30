const express = require('express');
const router = express.Router();
const { check } = require('express-validator');
const cleaningTaskController = require('../controllers/cleaningTaskController');
const { authenticate, authorize } = require('../middleware/auth');
const { ROLES } = require('../models/User');

// @route   POST /api/cleaning-tasks
// @desc    Create a new cleaning task
// @access  Private/Property Owner
router.post(
  '/',
  authenticate,
  authorize(ROLES.PROPERTY_OWNER),
  [
    check('propertyId', 'Property ID is required').not().isEmpty(),
    check('scheduledDate', 'Scheduled date is required').not().isEmpty()
  ],
  cleaningTaskController.createCleaningTask
);

// @route   GET /api/cleaning-tasks
// @desc    Get all cleaning tasks for property owner's properties
// @access  Private/Property Owner
router.get(
  '/',
  authenticate,
  authorize(ROLES.PROPERTY_OWNER),
  cleaningTaskController.getOwnerCleaningTasks
);

// @route   GET /api/cleaning-tasks/assigned
// @desc    Get all cleaning tasks assigned to the cleaner
// @access  Private/Cleaner
router.get(
  '/assigned',
  authenticate,
  authorize(ROLES.CLEANER),
  cleaningTaskController.getAssignedCleaningTasks
);

// @route   PUT /api/cleaning-tasks/:id
// @desc    Update a cleaning task
// @access  Private/Property Owner or assigned Cleaner
router.put(
  '/:id',
  authenticate,
  authorize(ROLES.PROPERTY_OWNER, ROLES.CLEANER),
  [
    check('status', 'Status must be valid').optional().isIn(['pending', 'in_progress', 'completed', 'cancelled'])
  ],
  cleaningTaskController.updateCleaningTask
);

// @route   DELETE /api/cleaning-tasks/:id
// @desc    Delete a cleaning task
// @access  Private/Property Owner
router.delete(
  '/:id',
  authenticate,
  authorize(ROLES.PROPERTY_OWNER),
  cleaningTaskController.deleteCleaningTask
);

module.exports = router;
