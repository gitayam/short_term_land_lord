const { validationResult } = require('express-validator');
const Property = require('../models/Property');
const Reservation = require('../models/Reservation');
const CleaningTask = require('../models/CleaningTask');
const { ROLES } = require('../models/User');

// @desc    Import calendar data and create reservations
// @route   POST /api/calendar/import
// @access  Private/Property Owner
exports.importCalendarData = async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const { propertyId, reservations, source } = req.body;

  try {
    // Check if property exists and belongs to the user
    const property = await Property.findById(propertyId);
    if (!property) {
      return res.status(404).json({ msg: 'Property not found' });
    }

    if (property.owner.toString() !== req.user.id) {
      return res.status(403).json({ msg: 'Not authorized to import calendar data for this property' });
    }

    // Process each reservation
    const createdReservations = [];
    const createdCleaningTasks = [];

    for (const reservationData of reservations) {
      // Create reservation
      const newReservation = new Reservation({
        property: propertyId,
        checkInDate: new Date(reservationData.checkInDate),
        checkOutDate: new Date(reservationData.checkOutDate),
        guestName: reservationData.guestName,
        guestEmail: reservationData.guestEmail || '',
        guestPhone: reservationData.guestPhone || '',
        numberOfGuests: reservationData.numberOfGuests || 1,
        source: source || 'manual',
        sourceReservationId: reservationData.sourceReservationId || '',
        reservationUrl: reservationData.reservationUrl || '',
        notes: reservationData.notes || ''
      });

      const savedReservation = await newReservation.save();
      createdReservations.push(savedReservation);

      // Automatically create a cleaning task for the check-out date
      const cleaningTask = new CleaningTask({
        property: propertyId,
        reservation: savedReservation._id,
        scheduledDate: new Date(reservationData.checkOutDate),
        notes: `Cleaning required after guest checkout. Guest: ${reservationData.guestName}`,
        createdBy: req.user.id
      });

      const savedCleaningTask = await cleaningTask.save();
      createdCleaningTasks.push(savedCleaningTask);
    }

    res.status(201).json({
      reservations: createdReservations,
      cleaningTasks: createdCleaningTasks
    });
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
};

// @desc    Get all reservations for a property
// @route   GET /api/calendar/reservations/:propertyId
// @access  Private/Property Owner
exports.getReservations = async (req, res) => {
  try {
    const property = await Property.findById(req.params.propertyId);
    if (!property) {
      return res.status(404).json({ msg: 'Property not found' });
    }

    if (property.owner.toString() !== req.user.id) {
      return res.status(403).json({ msg: 'Not authorized to view reservations for this property' });
    }

    const reservations = await Reservation.find({ property: req.params.propertyId })
      .sort({ checkInDate: 1 });
    
    res.json(reservations);
  } catch (err) {
    console.error(err.message);
    if (err.kind === 'ObjectId') {
      return res.status(404).json({ msg: 'Property not found' });
    }
    res.status(500).send('Server error');
  }
};
