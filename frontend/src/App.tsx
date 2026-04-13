import { Routes, Route } from 'react-router-dom';

function App() {
  return (
    <div className="min-h-screen bg-dark-bg">
      <Routes>
        <Route
          path="*"
          element={
            <div className="flex items-center justify-center min-h-screen">
              <div className="text-center">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                  CRM Pro
                </h1>
                <p className="mt-4 text-text-secondary">System Loading...</p>
              </div>
            </div>
          }
        />
      </Routes>
    </div>
  );
}

export default App;
