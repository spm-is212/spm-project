Prerequisites
1.	Node.js - Download & Install Node.js and the npm package manager.

Set-up for frontend
Assuming that you have cloned this repository and navigated to the root of the project, navigate to this folder (/frontend/all-in-one)
cd frontend/all-in-one
Installing Dependencies
npm install
Run Application in localhost
npm run dev

Set-up for backend
Assuming that you have cloned this repository and navigated to the root of the project, navigate to this folder (/backend)
cd backend
Run the FastAPI app backend:
uvicorn backend.main:app --reload
The app will start at: http://127.0.0.1:8000
