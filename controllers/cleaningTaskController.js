const { validationResult } = require('express-validator');
const CleaningTask = require('../models/CleaningTask');
const Property = require('../models/Property');
const { ROLES } = require('../models/User');

// @desc    Create a new cleaning task
// @route   POST /api/cleaning-tasks
// @access  Private/Property Owner
exports.createCleaningTask = async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  try {
    const { propertyId, scheduledDate, notes, assignedTo } = req.body;

    // Check if property exists and belongs to the user
    const property = await Property.findById(propertyId);
    if (!property) {
      return res.status(404).json({ msg: 'Property not found' });
    }

    if (property.owner.toString() !== req.user.id) {
      return res.status(403).json({ msg: 'Not authorized to create tasks for this property' });
    }

    const newTask = new CleaningTask({
      property: propertyId,
      scheduledDate,
      notes,
      assignedTo,
      createdBy: req.user.id
    });

    const task = await newTask.save();
    res.status(201).json(task);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
};

// @desc    Get all cleaning tasks for property owner's properties
// @route   GET /api/cleaning-tasks
// @access  Private/Property Owner
exports.getOwnerCleaningTasks = async (req, res) => {
  try {
    // Find all properties owned by the user
    const properties = await Property.find({ owner: req.user.id }).select('_id');
    const propertyIds = properties.map(property => property._id);

    // Find all cleaning tasks for these properties
    const tasks = await CleaningTask.find({ property: { $in: propertyIds } })
      .populate('property', 'name address')
      .populate('assignedTo', 'name email')
      .populate('reservation', 'checkInDate checkOutDate guestName')
      .sort({ scheduledDate: 1 });

    res.json(tasks);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
};

// @desc    Get all cleaning tasks assigned to the cleaner
// @route   GET /api/cleaning-tasks/assigned
// @access  Private/Cleaner
exports.getAssignedCleaningTasks = async (req, res) => {
  try {
    const tasks = await CleaningTask.find({ assignedTo: req.user.id })
      .populate('property', 'name address')
      .populate('reservation', 'checkInDate checkOutDate guestName')
      .sort({ scheduledDate: 1 });

    res.json(tasks);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
};

// @desc    Update a cleaning task
// @route   PUT /api/cleaning-tasks/:id
// @access  Private/Property Owner or assigned Cleaner
exports.updateCleaningTask = async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  try {
    const task = await CleaningTask.findById(req.params.id);
    
    if (!task) {
      return res.status(404).json({ msg: 'Cleaning task not found' });
    }

    // Check authorization
    if (req.user.role === ROLES.PROPERTY_OWNER) {
      // Property owners can only update tasks for their properties
      const property = await Property.findById(task.property);
      if (!property || property.owner.toString() !== req.user.id) {
        return res.status(403).json({ msg: 'Not authorized to update this task' });
      }
    } else if (req.user.role === ROLES.CLEANER) {
      // Cleaners can only update tasks assigned to them
      if (task.assignedTo && task.assignedTo.toString() !== req.user.id) {
        return res.status(403).json({ msg: 'Not authorized to update this task' });
      }
      
      // Cleaners can only update status and notes
      const allowedUpdates = ['status', 'notes'];
      const requestedUpdates = Object.keys(req.body);
      const isValidOperation = requestedUpdates.every(update => allowedUpdates.includes(update));
      
      if (!isValidOperation) {
        return res.status(400).json({ msg: 'Invalid updates for cleaner role' });
      }
    }

    // If status is being changed to completed, set completedAt
    if (req.body.status === 'completed' && task.status !== 'completed') {
      req.body.completedAt = new Date();
    }

    // Update task
    const updatedTask = await CleaningTask.findByIdAndUpdate(
      req.params.id,
      { $set: req.body },
      { new: true }
    )
      .populate('property', 'name address')
      .populate('assignedTo', 'name email')
      .populate('reservation', 'checkInDate checkOutDate guestName');

    res.json(updatedTask);
  } catch (err) {
    console.error(err.message);
    if (err.kind === 'ObjectId') {
      return res.status(404).json({ msg: 'Cleaning task not found' });
    }
    res.status(500).send('Server error');
  }
};

// @desc    Delete a cleaning task
// @route   DELETE /api/cleaning-tasks/:id
// @access  Private/Property Owner
exports.deleteCleaningTask = async (req, res) => {
  try {
    const task = await CleaningTask.findById(req.params.id);
    
    if (!task) {
      return res.status(404).json({ msg: 'Cleaning task not found' });
    }

    // Check if the task belongs to a property owned by the user
    const property = await Property.findById(task.property);
    if (!property || property.owner.toString() !== req.user.id) {
      return res.status(403).json({ msg: 'Not authorized to delete this task' });
    }

    await task.remove();
    res.json({ msg: 'Cleaning task removed' });
  } catch (err) {
    console.error(err.message);
    if (err.kind === 'ObjectId') {
      return res.status(404).json({ msg: 'Cleaning task not found' });
    }
    res.status(500).send('Server error');
  }
};
