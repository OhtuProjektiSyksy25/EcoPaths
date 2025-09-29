/*
Component that renders a single input field
Props:
	-placeholder: string shown when no input has been given (string)
	-value: current input value (string)
	-onChange: callback function called with updated value on value change
*/
import React from "react";

interface InputContainerProps {
  placeholder: string;
  value: string;
  onChange: (value:string) => void;
}

const InputContainer: React.FC<InputContainerProps> = ({
  placeholder,
  value,
  onChange
  }) => {


  return (
    <div className="InputContainer">
      <input
      type="text"
      value={value}
      onChange={(e)=> onChange(e.target.value)}
      placeholder={placeholder}
			/>
    </div>
  );
};

export default InputContainer
