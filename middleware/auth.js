const jwt = require('jsonwebtoken');
const { User } = require('../models/User');

// Middleware to verify JWT token
exports.authenticate = async (req, res, next) => {
  // Get token from header
  const token = req.header('x-auth-token');

  // Check if no token
  if (!token) {
    return res.status(401).json({ msg: 'No token, authorization denied' });
  }

  try {
    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    // Add user from payload
    req.user = await User.findById(decoded.user.id).select('-password');
    if (!req.user) {
      return res.status(401).json({ msg: 'Token is not valid' });
    }
    
    next();
  } catch (err) {
    res.status(401).json({ msg: 'Token is not valid' });
  }
};

// Middleware to check if user has required role
exports.authorize = (...roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ msg: 'Not authorized' });
    }
    
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ msg: 'Not authorized for this role' });
    }
    
    next();
  };
};
