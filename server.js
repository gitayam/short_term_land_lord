const express = require('express');
const mongoose = require('mongoose');
require('dotenv').config();

// Set strictQuery to false to prepare for Mongoose 7
mongoose.set('strictQuery', false);

// Initialize Express app
const app = express();

// Middleware
app.use(express.json());

// Connect to MongoDB
mongoose.connect(process.env.MONGO_URI || 'mongodb://localhost:27017/short-term-land-lord', {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
  .then(() => console.log('MongoDB connected'))
  .catch(err => console.error('MongoDB connection error:', err));

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/users', require('./routes/users'));

// Default route
app.get('/', (req, res) => {
  res.send('<h1>Short-Term LandLord API</h1><p>API is running. Use /api/auth and /api/users endpoints to interact with the API.</p>');
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, '0.0.0.0', () => console.log(`Server running on 0.0.0.0:${PORT}`));
