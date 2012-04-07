Feature: Home screen
    On the home screen of the app I should see apps and some basic information
    about the instance of Molly

Scenario: Page shows all apps which display on home
    Given I am on the home screen
    Then I should see a list of apps

Scenario: Home page shows no apps which are hidden from home
    Given I am on the home screen
    Then I should not see any hidden apps
