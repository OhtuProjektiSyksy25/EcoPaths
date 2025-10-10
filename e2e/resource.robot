*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${SERVER}       localhost:3000
${DELAY}        0.5 seconds
${HOME_URL}     http://${SERVER}
${BROWSER}      chrome
${HEADLESS}     true

*** Keywords ***
Open And Configure Browser
    IF  $BROWSER == 'chrome'
        ${options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys, selenium.webdriver
        Call Method    ${options}    add_argument    --headless
        Call Method    ${options}    add_argument    --no-sandbox
        Call Method    ${options}    add_argument    --disable-dev-shm-usage
        Call Method    ${options}    add_argument    --disable-gpu
        Call Method    ${options}    add_argument    --user-data-dir=/tmp/chrome-test-robot
        Set Selenium Speed    0
        Open Browser    ${HOME_URL}    ${BROWSER}    options=${options}
    ELSE IF  $BROWSER == 'firefox'
        ${options}=    Evaluate    sys.modules['selenium.webdriver'].FirefoxOptions()    sys, selenium.webdriver
        Call Method    ${options}    add_argument    --headless
        Set Selenium Speed    0
        Open Browser    ${HOME_URL}    ${BROWSER}    options=${options}
    ELSE
        Set Selenium Speed    ${DELAY}
        Open Browser    ${HOME_URL}    ${BROWSER}
    END


    