# Changelog

## Sprint 3

### Frontend

- RouteForm has been refactored into SideBar
- Time estimate appears on the sidebar only when a route exists
- The location button has been moved from SideBar to MapComponent
    - Clicking the location button no longer inserts the user's coordinates into the From input box
- The From input box displays "Your location" as the first suggestion
    - Clicking "Your location" sets the From field to the user's coordinates
- MapComponent has been adjusted to remove vertical scrolling
- All frontend css files are now in frontend/src/styles/
- Some tests have been added for SideBar, LocationButton and MapComponent