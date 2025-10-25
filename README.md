# All-In-One

## Prerequisites
Before you begin, ensure you have the following installed:
- **Node.js** (v18 or higher recommended)
- **npm** (comes with Node.js) or **yarn**

### Install Dependencies

Navigate to the frontend directory and install the required packages:


```bash
cd frontend/all-in-one
npm install
```

### Frontend: Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173` (or another port if 5173 is in use).

### Backend: Run the FastAPI App

Start the development server:

```bash
uvicorn backend.main:app --reload

```
The app will start at:
http://127.0.0.1:8000

### Viewing the Coverage Report

After running tests, an HTML coverage report is automatically generated at:

htmlcov/index.html


To open it locally:
macOS:
```bash
open htmlcov/index.html
```
Windows:
```bash
start htmlcov/index.html```