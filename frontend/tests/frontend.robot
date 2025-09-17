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
    Page Should Contain Element    css=.leaflet-container