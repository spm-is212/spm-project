import { Routes, Route } from "react-router-dom";
import LoginPage from './components/signuppage/login'
import TaskManager from './components/TaskManagement/TaskManager'
import ArchivedTasksView from './components/TaskManagement/ArchivedTasksView'

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/taskmanager" element={<TaskManager />} />
        <Route path="/archived-tasks" element={<ArchivedTasksView />} />
      </Routes>
    </div>
  );
}

export default App;
