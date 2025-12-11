# ClipCatcher

ClipCatcher is a web platform for Valorant streamers that automatically turns long stream VODs into highlight clips, provides a TikTok-style vertical editor, and includes a social feed of the best clips plus user profiles and a token-based subscription system.

## Features

- **Video Upload & Processing**: Upload long stream videos (up to 5 hours) for AI-powered highlight detection
- **TikTok-Style Editor**: Vertical layout editor with facecam and gameplay layers, auto-generated subtitles
- **User Accounts**: Email/password signup with Google OAuth support
- **Token System**: 100 free tokens for new users, with subscription and direct purchase options
- **User Dashboard**: Personal area to upload videos, browse clips, and manage content
- **Social Feed**: Global feed of all generated clips with engagement features
- **Public Profiles**: User profiles showcasing top clips and activity

## Tech Stack

### Backend
- Python FastAPI
- SQLAlchemy for database ORM
- SQLite for development database
- JWT for authentication
- Alembic for database migrations

### Frontend
- React with TypeScript
- Tailwind CSS for styling
- React Router for navigation
- shadcn/ui components
- Lucide React icons

## Project Structure

```
clipcatcher/
├── backend/
│   ├── api/          # API endpoints
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas
│   ├── utils/        # Utility functions
│   ├── database.py   # Database configuration
│   ├── dependencies.py # FastAPI dependencies
│   ├── main.py       # FastAPI application
│   └── requirements.txt
├── src/
│   ├── components/   # React components
│   ├── pages/        # Page components
│   ├── hooks/        # Custom hooks
│   ├── utils/        # Utility functions
│   ├── App.tsx       # Main application component
│   └── main.tsx      # Entry point
├── public/           # Static assets
└── README.md
```

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```

The backend API will be available at `http://localhost:8000`.

### Frontend Setup

1. Install frontend dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`.

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login user

### Users
- `GET /users/me` - Get current user info
- `GET /users/{user_id}` - Get user by ID

### Videos
- `POST /videos/upload` - Upload a video for processing

### Clips
- `GET /clips/feed` - Get global clips feed
- `GET /clips/user/{user_id}` - Get clips for a specific user
- `GET /clips/my-clips` - Get current user's clips

## Development

### Database Migrations

To create and run database migrations:

1. Initialize Alembic (if not already done):
   ```bash
   alembic init alembic
   ```

2. Create a new migration:
   ```bash
   alembic revision --autogenerate -m "Migration message"
   ```

3. Apply migrations:
   ```bash
   alembic upgrade head
   ```

## Deployment

### Backend

For production deployment, use a WSGI server like Gunicorn:

```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend

Build the frontend for production:

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License.