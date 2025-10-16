
/*
Root component for the React application. 
It renders the header and the MapComponent.
*/
import { useState } from "react";
import MapComponent from "./components/MapComponent";
import SideBar from "./components/SideBar";
import { useRoute } from "./hooks/useRoute";
import { LockedLocation } from "./types";
import "./styles/App.css";

/**
 * Root component of the EcoPaths React application.
 *
 * Manages the state of selected start and end locations,
 * fetches the route using a custom hook, and renders the UI including:
 * - Header
 * - RouteForm for selecting locations
 * - MapComponent for visualizing the route
 *
 * @returns JSX.Element representing the full application layout
 */
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

      <main className="main-container">

        <SideBar
          onFromSelect={setFromLocked}
          onToSelect={setToLocked}
          route={route}
        >
        {(loading || error) && (
          <div className="route-loading-message">
            {loading && <p>Loading route...</p>}
            {error && <p className="error">{error}</p>}
          </div>
        )}
        </SideBar>

        <div className="map-container">
          <MapComponent
            fromLocked={fromLocked}
            toLocked={toLocked}
            route={route}
          />
        </div>
      </main>
    </div>
  );
}

export default App;