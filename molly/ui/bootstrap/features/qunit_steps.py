from lettuce import step, world
from lettuce.django import django_url

@step(u'When I run the Qunit test runner')
def when_i_run_the_qunit_test_runner(step):
    world.browser.visit(django_url('tests'))

@step(u'Then I should see no failed tests')
def then_i_should_see_no_failed_tests(step):
    assert world.browser.find_by_css('#qunit-testresult .failed').first.value == '0'
