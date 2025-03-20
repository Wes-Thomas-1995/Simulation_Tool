import React, { createContext, useState } from 'react';



const Layout = ({ children }) => {


  return (
    <div className="min-h-screen bg-base-200 flex">
      {/* Sidebar */}

      {/* Main Content */}
      <div
        className={`transition-all duration-300 flex-grow`}
        style={{
          marginLeft: '1rem',
          padding: '1rem',
        }}
      >
        <div className="bg-base-200 shadow-lg rounded-lg p-6">
          {React.cloneElement(children ) || (
            <p>This is placeholder content for the main content area.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Layout;