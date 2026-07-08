# ILIAS Portal — Angular 17 Frontend

A production-grade Angular 17 frontend for managing ILIAS LMS courses at Tübingen University.

## Features

- 🔐 **Authentication** — JWT-based login / registration with token interceptor
- 🎓 **Course Management** — Browse, sync, and explore ILIAS courses
- 📝 **Content Publishing** — Create assignments, upload slides, post announcements
- 🔑 **ILIAS Credentials** — Securely manage your university (zx...) login
- 🌙 **Dark academic theme** — Professional UI with Inter font and CSS variables
- 📱 **Responsive** — Works on desktop and mobile

## Tech Stack

| Tool | Version |
|------|---------|
| Angular | 17.x (standalone components) |
| TypeScript | 5.4.x |
| RxJS | 7.8.x |
| Font Awesome | 6.5.x |
| Inter font | Google Fonts |

## Project Structure

```
src/
  app/
    core/
      services/       auth.service, ilias.service, token-interceptor
      guards/         auth.guard (functional)
      models/         user.model, course.model
    features/
      auth/           login, register
      dashboard/      overview with stats & quick actions
      credentials/    ILIAS credential management
      courses/        course list with refresh
      course-detail/  accordion content view + publish modal
    shared/
      components/     navbar
      pipes/          totalItems
```

## Getting Started

```bash
# Install dependencies
npm install

# Start dev server (requires Node 18+)
npm start

# Build for production
npm run build
```

Backend must be running at `http://localhost:8000`.

## API Endpoints Expected

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/login/` | Obtain JWT tokens |
| POST | `/api/auth/register/` | Register new user |
| GET | `/api/auth/profile/` | Get user profile |
| POST | `/api/auth/ilias-credentials/` | Save ILIAS credentials |
| GET | `/api/auth/ilias-credentials/` | Get ILIAS credentials |
| GET | `/api/ilias/courses/` | List cached courses |
| POST | `/api/ilias/courses/refresh/` | Sync courses from ILIAS |
| GET | `/api/ilias/courses/:id/contents/` | Course content tree |
| POST | `/api/ilias/courses/:id/publish/assignment/` | Create assignment |
| POST | `/api/ilias/courses/:id/publish/slides/` | Upload slides |
| POST | `/api/ilias/courses/:id/publish/announcement/` | Post announcement |
