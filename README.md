# Short Term Land Lord

A property management application for short-term rental properties with secure user authentication and role-based access control.

## Features

- User authentication (registration and login)
- Role-based access control with three user roles:
  - Property Owners: Users who own properties managed in the system
  - Cleaners: Staff responsible for cleaning properties
  - Maintenance Personnel: Staff responsible for property maintenance and repairs
- Secure password storage using bcrypt hashing

## Technical Stack

- Node.js with Express
- MongoDB with Mongoose
- JSON Web Tokens (JWT) for authentication
- bcrypt for password hashing

## Project Structure

```
├── config/             # Configuration files
├── controllers/        # Request handlers
├── middleware/         # Express middleware
├── models/             # Database models
├── routes/             # API routes
├── utils/              # Utility functions
└── server.js           # Entry point
```

## Authentication System

The application implements a secure authentication system with:
- User registration with validation
- Secure login with JWT token generation
- Password hashing using bcrypt
- Role-based access control

## Getting Started

1. Clone the repository
2. Install dependencies: `npm install`
3. Set up environment variables
4. Start the server: `npm start`

## Docker Setup

### Prerequisites
- Docker and Docker Compose installed on your system

### Running with Docker Compose
1. Clone the repository
2. Build and start the containers:
   ```
   docker-compose up -d
   ```
3. The application will be available at http://localhost:5000

### Environment Variables
The following environment variables are used in the Docker setup:
- `PORT`: The port on which the application runs (default: 5000)
- `MONGO_URI`: MongoDB connection string (default: mongodb://mongodb:27017/short-term-land-lord)
- `JWT_SECRET`: Secret key for JWT token generation and verification

These variables can be configured in the docker-compose.yml file or through a .env file.