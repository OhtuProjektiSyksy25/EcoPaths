
/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import  {useState, useEffect} from "react";
import MapComponent from "./components/MapComponent";
import RouteForm from "./components/RouteForm";
import "./App.css";




function App(): JSX.Element {
    const [fromLocked, setFromLocked] = useState<any>([])
    const [toLocked, setToLocked] = useState<any>([])
    const [route, setRoute] = useState<any>(null) //todo fix type
    
    useEffect(() => {
      if (fromLocked && toLocked && fromLocked?.full_address && toLocked?.full_address) {
        const getRoute = async() => {
          try {
          const fromCoordinatesString = `${fromLocked.geometry.coordinates[0]},${fromLocked.geometry.coordinates[1]}`
          const toCoordinatesString = `${toLocked.geometry.coordinates[0]},${toLocked.geometry.coordinates[1]}`
          const response = await fetch(`${process.env.REACT_APP_API_URL}/getroute/${fromCoordinatesString}/${toCoordinatesString}`)
          if (!response.ok) {
            throw new Error(`server error: ${response.status}`)
          } 
          const data = await response.json()
          // server returns { route, route_aq } — keep both so MapComponent can draw both
          setRoute(data)
          } catch (error) {
          console.log(error)}
        }
      getRoute()

      }
      

    },[fromLocked, toLocked])


  return (
    <div className="App">
      <header className="header">
        <h1 className="title">EcoPaths</h1>
      </header>
      <main>
        <div className="controls-container">
        <RouteForm
          onFromSelect={setFromLocked}
          onToSelect={setToLocked}
          route={route}/>
        </div>
      <MapComponent
        fromLocked={fromLocked} 
        toLocked={toLocked} 
        route={route}/>
        </main>
    </div>
  );
}
export default App;


