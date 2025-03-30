const mongoose = require('mongoose');

const ReservationSchema = new mongoose.Schema({
  property: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Property',
    required: true
  },
  checkInDate: {
    type: Date,
    required: true
  },
  checkOutDate: {
    type: Date,
    required: true
  },
  guestName: {
    type: String,
    required: true
  },
  guestEmail: {
    type: String,
    trim: true,
    lowercase: true
  },
  guestPhone: {
    type: String,
    trim: true
  },
  numberOfGuests: {
    type: Number,
    default: 1
  },
  source: {
    type: String,
    enum: ['airbnb', 'zillow', 'manual', 'other'],
    default: 'manual'
  },
  sourceReservationId: {
    type: String,
    trim: true
  },
  reservationUrl: {
    type: String,
    trim: true
  },
  notes: {
    type: String,
    trim: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Reservation', ReservationSchema);
