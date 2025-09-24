import { Routes, Route } from "react-router-dom";
import LoginPage from './components/signuppage/login'
import TaskManager from './components/TaskManagement/TaskManager'

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/taskmanager" element={<TaskManager />} />
      </Routes>
    </div>
  );
}

export default App;
