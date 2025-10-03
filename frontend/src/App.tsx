
/*
Root component for the React application. 
It renders the header and the MapComponent.
*/

import MapComponent from "./components/MapComponent";
import RouteForm from "./components/RouteForm";
import "./App.css";
import DisplayContainer from "./components/displayContainer";



function App(): JSX.Element {
  return (
    <div className="App">
      <header className="header">
        <h1 className="title">EcoPaths</h1>
      </header>
      <div className="controls-row">
        <RouteForm/>
        <DisplayContainer label="Walking Time" value="Place Holder" />
      </div>
      <MapComponent />
    </div>
  );
}
export default App;


