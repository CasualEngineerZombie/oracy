# OracyAI prototype (Lovable export)

This repo contains a Vite + React + TypeScript prototype for an “oracy assessment + feedback” flow, with pupil and teacher journeys and a live audio-recording demo that uses simulated (sample) AI output.

It’s a front-end prototype: there is no real backend, transcription service, or model integration wired in yet. Anywhere you see “processing”, “results”, or “evidence pins”, those are currently driven by local sample data.

## Tech stack

- Vite + React + TypeScript
- TailwindCSS + shadcn/ui (Radix UI components)
- react-router-dom for routing
- @tanstack/react-query (set up, not heavily used)
- framer-motion for animations
- vitest + testing-library for tests
- ESLint

## Quick start

Prereqs:
- Node.js (recommended: 18+)

Install dependencies (pick one approach and stick to it):
- npm:
  - npm install
  - npm run dev
- bun (bun.lockb is included):
  - bun install
  - bun run dev

Then open the local URL Vite prints (typically http://localhost:5173).

## Useful scripts

- npm run dev
  - run the dev server
- npm run build
  - production build
- npm run preview
  - preview the production build locally
- npm run lint
  - lint the project
- npm run test
  - run tests once
- npm run test:watch
  - run tests in watch mode

## Main routes / pages

The app uses react-router. Key routes:

- /
  - Landing page (high-level overview)
- /live-demo
  - live demo flow (consent → record audio → simulated processing → results)
  - requires microphone permission in the browser
- /pupil
  - pupil dashboard
- /pupil/task/:id
  - task recording page (prototype UI)
- /pupil/feedback/:id
  - feedback page (prototype UI)
- /pupil/progress
  - progress page (pupil view)
- /teacher
  - teacher dashboard
- /teacher/review/:id
  - teacher review page (prototype UI)
- /teacher/progress
  - progress page (teacher view)

If you hit a dead route you’ll land on:
- *
  - NotFound page

Routing is defined in src/App.tsx.

## Where the “AI output” is currently coming from

The live demo does not call any external API. It uses local sample data and a fake “processing” delay:

- src/data/sampleDemoResult.ts
  - SAMPLE_RESULT: transcript, confidence, delivery stats, strengths, next steps, evidence pins, etc.
  - simulateProcessing(): helper used to mimic async processing

When we will plug in a real pipeline (record → upload → transcribe → score → evidence), this is the file to replace/extend first.

## Audio recording (live demo)

The live demo uses the browser MediaRecorder API via:

- src/hooks/useAudioRecorder.ts

Notes:
- you’ll be prompted for microphone permission
- recordings are capped (default max is 60 seconds)
- this is intended for demo/prototype use for sales/bizdev; production capture/upload should include error handling, device compatibility, and secure storage.

## Project structure (high level)

- src/pages/
  - top-level route components (LandingPage, LiveDemoPage, PupilDashboard, TeacherDashboard, etc.)
- src/components/
  - UI building blocks (layout, badges, cards, etc.)
- src/hooks/
  - reusable hooks (audio recorder)
- src/data/
  - sample data used for demo results
- public/
  - static assets (favicon, etc.)
- src/assets/
  - brand assets (logos)

## What’s missing (by design)

- backend / database
- authentication / roles
- real transcription (ASR)
- real scoring / benchmarking logic
- real teacher moderation workflow persistence
- analytics / logging
- secure file storage
