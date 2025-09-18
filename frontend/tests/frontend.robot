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

Berlin tile png is visible
    Go To   ${HOME_URL}
    Wait Until Element Is Visible    css=.leaflet-tile-container.leaflet-zoom-animated img.leaflet-tile    timeout=5s
    ${tiles}=    Get WebElements    css=.leaflet-tile-container.leaflet-zoom-animated img.leaflet-tile 
    ${flag}=    Set Variable    False
    FOR    ${tile}    IN    @{tiles}
        ${src}=    Get Element Attribute    ${tile}    src
        Run Keyword If    '${src}'=='https://c.tile.openstreetmap.org/14/8801/5373.png'    Set Test Variable    ${flag}    True
        Run Keyword If    ${flag}    Exit For Loop
    END
    Should Be True    ${flag}
