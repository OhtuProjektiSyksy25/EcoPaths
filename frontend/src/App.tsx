
/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import  {useState} from "react";
import MapComponent from "./components/MapComponent";
import RouteForm from "./components/RouteForm";
import "./App.css";



function App(): JSX.Element {
    const [fromLocked, setFromLocked] = useState<any>([])
    const [toLocked, setToLocked] = useState<any>([])
    
  return (
    <div className="App">
      <header className="header">
        <h1 className="title">EcoPaths</h1>
      </header>
      <RouteForm
        onFromSelect={setFromLocked}
        onToSelect={setToLocked}/>
      <MapComponent
        fromLocked={fromLocked} 
        toLocked={toLocked} />
    </div>
  );
}
export default App;


