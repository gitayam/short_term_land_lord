const { validationResult } = require('express-validator');
const Property = require('../models/Property');

// @desc    Create a new property
// @route   POST /api/properties
// @access  Private/Property Owner
exports.createProperty = async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  try {
    const newProperty = new Property({
      ...req.body,
      owner: req.user.id
    });

    const property = await newProperty.save();
    res.status(201).json(property);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
};

// @desc    Get all properties for the logged-in property owner
// @route   GET /api/properties
// @access  Private/Property Owner
exports.getProperties = async (req, res) => {
  try {
    const properties = await Property.find({ owner: req.user.id });
    res.json(properties);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
};

// @desc    Get a single property by ID
// @route   GET /api/properties/:id
// @access  Private/Property Owner
exports.getPropertyById = async (req, res) => {
  try {
    const property = await Property.findById(req.params.id);
    
    if (!property) {
      return res.status(404).json({ msg: 'Property not found' });
    }

    // Check if the property belongs to the logged-in user
    if (property.owner.toString() !== req.user.id) {
      return res.status(403).json({ msg: 'Not authorized to access this property' });
    }

    res.json(property);
  } catch (err) {
    console.error(err.message);
    if (err.kind === 'ObjectId') {
      return res.status(404).json({ msg: 'Property not found' });
    }
    res.status(500).send('Server error');
  }
};

// @desc    Update a property
// @route   PUT /api/properties/:id
// @access  Private/Property Owner
exports.updateProperty = async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  try {
    let property = await Property.findById(req.params.id);
    
    if (!property) {
      return res.status(404).json({ msg: 'Property not found' });
    }

    // Check if the property belongs to the logged-in user
    if (property.owner.toString() !== req.user.id) {
      return res.status(403).json({ msg: 'Not authorized to update this property' });
    }

    // Update property
    property = await Property.findByIdAndUpdate(
      req.params.id,
      { $set: req.body },
      { new: true }
    );

    res.json(property);
  } catch (err) {
    console.error(err.message);
    if (err.kind === 'ObjectId') {
      return res.status(404).json({ msg: 'Property not found' });
    }
    res.status(500).send('Server error');
  }
};

// @desc    Delete a property
// @route   DELETE /api/properties/:id
// @access  Private/Property Owner
exports.deleteProperty = async (req, res) => {
  try {
    const property = await Property.findById(req.params.id);
    
    if (!property) {
      return res.status(404).json({ msg: 'Property not found' });
    }

    // Check if the property belongs to the logged-in user
    if (property.owner.toString() !== req.user.id) {
      return res.status(403).json({ msg: 'Not authorized to delete this property' });
    }

    await property.remove();
    res.json({ msg: 'Property removed' });
  } catch (err) {
    console.error(err.message);
    if (err.kind === 'ObjectId') {
      return res.status(404).json({ msg: 'Property not found' });
    }
    res.status(500).send('Server error');
  }
};
