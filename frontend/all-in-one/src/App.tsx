import { Routes, Route, Link } from "react-router-dom";
import Auth from "./pages/Auth";


function App() {
  return (
    <div>
      {/* navbar */}
      <nav>

        <Link to="/auth">Auth</Link> {" "}
      </nav>

      {/* routing */}
      <Routes>

        <Route path="/auth" element={<Auth />} />
      </Routes>
    </div>
  );
}

export default App;
