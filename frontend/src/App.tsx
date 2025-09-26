
/*
Root component for the React application. 
It renders the header and the MapComponent.
*/

import MapComponent from "./components/MapComponent";
import RouteForm from "./components/RouteForm";
import "./App.css";



function App(): JSX.Element {
  return (
    <div className="App">
      <header className="header">
        <h1 className="title">EcoPaths</h1>
      </header>
      <RouteForm/>
      <MapComponent />
    </div>
  );
}
export default App;


