import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import EcoPathsApp from './EcoPathsApp';
import AdminDashboard from './components/AdminDashboard';

function App(): JSX.Element {
  return (
    <Router>
      <Routes>
        <Route path='/admin' element={<AdminDashboard />} />
        <Route path='/*' element={<EcoPathsApp />} />
      </Routes>
    </Router>
  );
}

export default App;
