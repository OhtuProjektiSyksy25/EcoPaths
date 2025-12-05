import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import AdminDashboard from "./components/AdminDashboard";   // NEW - use page version
import EcoPathsApp from "./EcoPathsApp";               // NEW - move existing App content here

function App(): JSX.Element {
  return (
    <Router>
      <Routes>
        {/* Admin route */}
        <Route path="/admin" element={<AdminDashboard />} />

        {/* Default app route */}
        <Route
          path="/*"
          element={<EcoPathsApp />}
        />
      </Routes>
    </Router>
  );
}
export default App;

