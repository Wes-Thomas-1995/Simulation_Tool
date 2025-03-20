// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Simulations from './pages/SIMULATIONS/Simulations';


function App() {
  return (
    <Router>
      <Layout>
        <Routes>

          <Route path="/SIMULATIONS" element={<Simulations />} />

        </Routes>
      </Layout>
    </Router>
  );
}

export default App;