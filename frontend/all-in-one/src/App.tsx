import { Routes, Route } from "react-router-dom";
import LoginPage from './components/signuppage/login'
import TaskManager from './components/TaskManagement/TaskManager'
import TeamView from './components/TaskManagement/TeamView.tsx';


function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/taskmanager" element={<TaskManager />} />
        <Route path="/team" element={<TeamView />} />
      </Routes>
    </div>
  );
}

export default App;
