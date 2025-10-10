Run the FastAPI App Backend

Start the development server:

```bash
uvicorn backend.main:app --reload

```
The app will start at:
http://127.0.0.1:8000

Viewing the Coverage Report

After running tests, an HTML coverage report is automatically generated at:

htmlcov/index.html


To open it locally:
```bash
macOS:

open htmlcov/index.html
```
```bash
Windows:

start htmlcov/index.html```
