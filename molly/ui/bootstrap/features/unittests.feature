Feature: JavaScript unit tests should pass

Scenario: Run the JavaScript unit tests
    When I run the Qunit test runner
    Then I should see no failed tests
