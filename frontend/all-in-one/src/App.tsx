import { Routes, Route, Link } from "react-router-dom";
import TaskManager from "./components/TaskManager";
import Auth from "./pages/Auth.tsx";
import "./styles/Task.css"; // Import the new task styles

function App() {
  return (
    <div>
      {/* navbar */}
      <nav>
        <Link to="/">Task Manager</Link> |{" "}
        <Link to="/auth">Auth</Link> {" "}
      </nav>

      {/* routing */}
      <Routes>
        <Route path="/" element={<TaskManager />} />
        <Route path="/auth" element={<Auth />} />
      </Routes>
    </div>
  );
}

export default App;
