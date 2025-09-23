*** Settings ***
Resource    resource.robot
Suite Setup      Open And Configure Browser
Suite Teardown    Close Browser



*** Test Cases ***
Frontend loads correct
    Go To    ${HOME_URL}
    Title Should Be    EcoPaths

Header is visible
    Go To    ${HOME_URL}
    Element Should Contain    css=h1.title    EcoPaths

Map component is visible
    Go To    ${HOME_URL}
    Wait Until Element Is Visible    css:.mapboxgl-map    timeout=10s

Berlin tile png is visible and has loaded content
    Wait Until Element Is Visible    css=.mapboxgl-canvas-container canvas    timeout=10s
    Wait Until Element Is Visible    css=.mapboxgl-control-container    timeout=5s
     ${canvases}=    Get WebElements    css=.mapboxgl-canvas-container canvas
    Length Should Be    ${canvases}    1

