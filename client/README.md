# Short-Term LandLord Frontend

This is the frontend application for the Short-Term LandLord property management system. It provides a user interface for property owners to manage their properties, view calendars, and handle reservations.

## Features

- User authentication (login/register)
- Dashboard to view property statistics
- Calendar interface to view and manage reservations
- Responsive design with Mantine UI components

## Technologies Used

- React
- TypeScript
- React Router for navigation
- Axios for API communication
- React Big Calendar for calendar functionality
- Mantine UI for components
- Tailwind CSS for styling

## Development

### Prerequisites

- Node.js 18+ installed
- npm or yarn

### Getting Started

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. Build for production:
   ```
   npm run build
   ```

## Docker

This frontend is dockerized and can be run using Docker:

```bash
# Build the Docker image
docker build -t short-term-landlord-frontend .

# Run the container
docker run -p 3000:80 short-term-landlord-frontend
```

Or simply use docker-compose from the root project directory:

```bash
docker-compose up
```

This will start both the frontend and backend services.

## Backend Integration

The frontend communicates with the backend API through proxy configurations. In the development environment, API requests are proxied to `http://localhost:5888`, while in the production Docker environment, requests are proxied to the backend service via Nginx. 