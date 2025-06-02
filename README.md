# La Liga Predictor

A responsive React application that fetches La Liga fixtures and displays past results, upcoming matches, and matchday data—complete with team crests, score bubbles, and prediction bubbles. The UI uses Tailwind CSS for clean styling and features a light “white card” theme to complement team logos. The backend is built with Python and Flask, serving REST endpoints for teams and fixtures.

---

## Features

- **Team Selector:** Pick any La Liga team from a dropdown and view that team’s previous five results and next five fixtures.
- **Latest Matchday Card Grid:** Display all matches from the most recent matchday (e.g., Matchday 38) in a responsive grid.
- **Score Bubbles:** Each card shows a “Home – Score – Away” bubble, styled to stand out against white backgrounds.
- **Prediction Bubbles:** Below the crests, each card displays a red-bordered prediction (e.g., “Predicted: Real Betis Balompié to win”).
- **Loading Screen:** A six-second “Loading” overlay with animated messages and a red progress bar—perfect for initial data fetching.
- **Responsive Design:** Grid layout collapses gracefully on small screens (1 column on mobile, 2 on tablets, 3 on desktop).
- **Python/Flask Backend:** REST API endpoints provide team lists and fixture data (last 5 results, next 5 fixtures, latest matchday).

---

## Technologies Used

- **Frontend:**  
  - React (v17+)  
  - Tailwind CSS (utility-first styling, custom color palette)  
  - Axios (for REST API calls)  
- **Backend:**  
  - Python 3.x  
  - Flask (serving REST endpoints)  
- **Tooling:**  
  - Node.js / npm (package management)  
  - Vite or Create React App (boilerplate—you can adapt to your preferred React tooling)  
  - pip (for Python dependencies)  

---
