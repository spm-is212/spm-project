import { Routes, Route, Link } from "react-router-dom";
import MyTasks from "./pages/MyTasks.tsx";
import Auth from "./pages/Auth.tsx";

function App() {
  return (
    <div>
      {/* navbar */}
      <nav>
        <Link to="/">MyTasks</Link> |{" "}
        <Link to="/auth">Auth</Link> {" "}
      </nav>

      {/* routing */}
      <Routes>
        <Route path="/" element={<MyTasks />} />
        <Route path="/auth" element={<Auth />} />
      </Routes>
    </div>
  );
}

export default App;
