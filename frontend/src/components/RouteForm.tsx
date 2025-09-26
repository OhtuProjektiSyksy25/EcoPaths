/*
Component that renders "From" and "To" input fields and manages their state
*/

import React, { useState } from "react";
import InputContainer from "./InputContainer";

const RouteForm: React.FC = () => {

  const [from, setFrom] = useState<string>("")
  const [to, setTo] = useState<string>("")

  return (
    <div>
      <InputContainer
      placeholder = "From..."
      value = {from}
      onChange = {setFrom}
      />
      <InputContainer
      placeholder = "To..."
      value = {to}
      onChange = {setTo}
      />
    </div>
  );
};

export default RouteForm