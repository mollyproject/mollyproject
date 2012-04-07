from lettuce import before, after, world
from splinter.browser import Browser

@before.all
def initial_setup():
    world.browser = Browser('webdriver.firefox')
    
    def get_container():
        return world.browser.find_by_id('body').first
    world.container = get_container

@after.all
def teardown_browser(total):
    world.browser.quit()
