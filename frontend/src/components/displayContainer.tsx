/*
DisplayContainer is a component that displays information, for example the walking time estimate to the user. 
*/

import React from 'react';

interface DisplayContainerProps {
  label: string;
  value: string;
}

const DisplayContainer: React.FC<DisplayContainerProps> = ({ label, value }) => {
  return (
    <div className="DisplayContainer">
      <span className="label">{label}: </span>
      <span className="value">{value}</span>
    </div>
  );
};

export default DisplayContainer;