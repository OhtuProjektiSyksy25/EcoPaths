*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${SERVER}       localhost:3000
${DELAY}        0.5 seconds
${HOME_URL}     http://${SERVER}
${BROWSER}      chrome
${HEADLESS}     false

*** Keywords ***
Open And Configure Browser
    IF  $BROWSER == 'chrome'
        ${options}  Evaluate  sys.modules['selenium.webdriver'].ChromeOptions()  sys
    ELSE IF  $BROWSER == 'firefox'
        ${options}  Evaluate  sys.modules['selenium.webdriver'].FirefoxOptions()  sys
    END
    IF  $HEADLESS == 'true'
        Set Selenium Speed    0
        Call Method    ${options}    add_argument    --headless
    ELSE
        Set Selenium Speed    ${DELAY}
    END
    Open Browser    ${HOME_URL}    ${BROWSER}    options=${options}


    