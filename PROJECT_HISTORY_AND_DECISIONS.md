# Project History & Technical Decisions

This document records the main decisions, problems, solutions, and technical context of the VideoToNotes.ai backend project. It is intended to provide onboarding and historical context for any developer joining or maintaining the system.

---

## 1. Project Overview

VideoToNotes.ai is a robust system for transcribing audio/video, summarizing content, generating flashcards, questions, and study plans. It features:
- Backend: FastAPI (Python), containerized, deployed on Google Cloud Run
- Frontend: Next.js (TypeScript), deployed on Netlify
- Authentication: Google/NextAuth, JWT integration between frontend and backend
- Main AI provider: OpenAI (Whisper for transcription, GPT for summarization)

---

## 2. Major Technical Decisions & Rationale

### 2.1. API Provider
- **OpenAI is the default and main provider** for both transcription and summarization.
- Local models (e.g., T5 for summarization, Whisper for transcription) are supported as fallback/alternative, but not recommended for production due to performance and resource constraints.
- All code and documentation prioritize OpenAI usage.

### 2.2. YouTube Support
- **YouTube transcription and metadata extraction was removed** due to:
  - Cloud Run and other cloud providers block automated YouTube downloads (yt-dlp, cookies, etc.)
  - Legal and technical risks
  - Focus shifted to direct file uploads (audio/video)
- All endpoints, code, and UI related to YouTube were deleted for clarity and maintainability.

### 2.3. File Size Limits
- OpenAI Whisper API has a **25MB file size limit**.
- The backend compresses audio extracted from video to maximize the chance of fitting under this limit.
- The frontend validates file size and informs the user of this restriction.

### 2.4. Authentication & Security
- JWT authentication is enforced on all main endpoints.
- NextAuth (Google) is used on the frontend; JWT is sent in the Authorization header to the backend.
- Secrets (OPENAI_API_KEY, NEXTAUTH_SECRET) are managed via Google Secret Manager, with correct IAM permissions for Cloud Run.
- FastAPI docs and OpenAPI endpoints are disabled in production for security.

### 2.5. CI/CD & Branch Protection
- Backend: GitHub Actions runs CI on every PR to main; branch protection requires PR and passing status check before merge.
- Frontend: Netlify deploy previews are used as the main check; GitHub Actions CI is optional.
- Auto-merge and branch deletion are configured via GitHub settings for workflow hygiene.

### 2.6. Docker & Deployment
- Backend is fully containerized; Dockerfile and docker-compose.prod.yml provided for local and production simulation.
- Frontend uses standard Next.js build on Netlify (no Docker needed for FE).
- All environment variables are injected via secrets or Netlify dashboard.

---

## 3. Problems Faced & Solutions

### 3.1. YouTube Download Blocked in Cloud
- Problem: yt-dlp and similar tools are blocked on Cloud Run and most cloud providers.
- Solution: Removed all YouTube-related features; focused on direct file upload.

### 3.2. OpenAI File Size Limit
- Problem: Whisper API rejects files >25MB.
- Solution: Audio is compressed to mono, 16kHz, 48kbps AAC before upload; frontend blocks large files and informs the user.

### 3.3. CI Status Not Appearing in Branch Protection
- Problem: GitHub branch protection did not recognize CI status.
- Solution: Explicit job name in workflow, ensured CI runs on PRs to main.

### 3.4. Secret Manager Permissions
- Problem: Cloud Run service account lacked access to secrets.
- Solution: Granted `roles/secretmanager.secretAccessor` to the service account.

### 3.5. Docker vs Standard Build for Frontend
- Problem: Netlify does not support custom Docker builds for Next.js by default.
- Solution: Use standard Next.js build on Netlify; Docker only for backend.

---

## 4. Production Checklist

- [x] Backend containerized and optimized for Cloud Run
- [x] Frontend deployed on Netlify with environment variables
- [x] CI/CD with branch protection and required status checks
- [x] Secrets managed via Google Secret Manager and Netlify dashboard
- [x] File size validation and compression for OpenAI API
- [x] JWT authentication enforced on all endpoints
- [x] FastAPI docs disabled in production
- [x] All YouTube logic removed for compliance and reliability
- [x] Logging and error handling in place (including performance logs)
- [x] README and documentation up to date

---

## 5. Technical Limitations & Considerations

- OpenAI Whisper API: 25MB file size limit, English language only by default (can be changed in code)
- Local models (T5, Whisper) are much slower and require significant RAM/CPU; not recommended for production
- Cloud Run has cold start latency; consider this for user experience
- No YouTube support due to cloud restrictions
- Audio extraction uses ffmpeg; ensure it is available in your environment

---

## 6. Integration Context (Frontend/Backend)

- Frontend authenticates via Google/NextAuth, obtains JWT, and sends it in the Authorization header to backend endpoints
- All main backend endpoints require JWT authentication
- File uploads are handled via multipart/form-data POST to `/transcribe`
- The backend returns both the transcription and summary in the response
- Additional endpoints exist for question, flashcard, and study plan generation, all requiring authentication

---

## 7. Future Improvements

- Add support for more languages and models
- Implement progressive upload and real-time feedback (WebSocket)
- Enhance error reporting and user feedback
- Add more granular logging and monitoring (e.g., integration with Google Cloud Logging)
- Expand test coverage and CI automation

---

## 8. Contact

Project lead: Camilo Raitz
Email: craitz@gmail.com
GitHub: https://github.com/craitz

---

End of document. 