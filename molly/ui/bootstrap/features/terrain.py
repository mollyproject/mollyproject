from lettuce import before, after, world
from splinter.browser import Browser

@before.all
def initial_setup():
    world.browser = Browser('webdriver.firefox')

@after.all
def teardown_browser(total):
    world.browser.quit()
