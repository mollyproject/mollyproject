from lettuce import step, world
from lettuce.django import django_url

from molly.conf.applications import all_apps

@step(u'Given I am on the home screen')
def given_i_am_on_the_home_screen(step):
    world.browser.visit(django_url('/'))

@step(u'Then I should see a list of apps')
def then_i_should_see_a_list_of_apps(step):
    
    for app in filter(lambda app: app.display_to_user, all_apps()):
        assert world.browser.is_text_present(app.title)

@step(u'Then I should not see any hidden apps')
def then_i_should_not_see_any_hidden_apps(step):
    for app in filter(lambda app: not app.display_to_user, all_apps()):
        assert not world.browser.is_text_present(app.title)

