import { Routes, Route } from "react-router-dom";
import LoginPage from './components/signuppage/login'
import TaskManager from './components/TaskManagement/TaskManager'
import TeamView from './components/TaskManagement/TeamView.tsx';
import Layout from './components/nav/Layout.tsx';
import CalendarView from './components/DeadlineSchedule/calendarView.tsx';

function App() {
  return (
    <div className="App">
      <Routes>
        {/* Login page without sidebar */}
        <Route path="/" element={<LoginPage />} />

        {/* Protected routes with sidebar */}
        <Route element={<Layout />}>
          <Route path="/taskmanager" element={<TaskManager />} />
          <Route path="/team" element={<TeamView />} />
          <Route path="/calendarview" element={<CalendarView />} />
        </Route>
      </Routes>
    </div>
  );
}

export default App;
