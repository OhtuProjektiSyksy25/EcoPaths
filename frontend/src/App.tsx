
/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import  {useState, useEffect} from "react";
import MapComponent from "./components/MapComponent";
import RouteForm from "./components/RouteForm";
import "./App.css";
import DisplayContainer from "./components/DisplayContainer";




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


          console.log(fromCoordinatesString)
          console.log(toCoordinatesString)
          const response = await fetch(`${process.env.REACT_APP_API_URL}/getroute/${fromCoordinatesString}/${toCoordinatesString}`)
          if (!response.ok) {
            throw new Error(`server error: ${response.status}`)
          } 
          const data = await response.json()
          console.log("fetched route data:", data.route?.properties?.time_estimate)
          console.log("full data:", data)
          setRoute(data.route)
          
          } catch (error) {
          console.log(error)}
        }
      
        const result = getRoute()
      }
      

    },[fromLocked, toLocked])


  return (
    <div className="App">
      <header className="header">
        <h1 className="title">EcoPaths</h1>
      </header>
      <RouteForm
        onFromSelect={setFromLocked}
        onToSelect={setToLocked}/>
      <DisplayContainer label="Walking Time" value={route?.properties?.time_estimate || "N/A"} />

      <MapComponent
        fromLocked={fromLocked} 
        toLocked={toLocked} 
        route={route}/>
    </div>
  );
}
export default App;


