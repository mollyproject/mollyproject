#!/usr/bin/env python

import sys
import urllib2

USER_AGENTS={
    
    # iPhone 3 - gets smart styling
    'smart': 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16',
    
    # iPaq - gets dumb styling
    'dumb': 'Mozilla/4.0 (compatible; MSIE 4.01; Windows CE; PPC; 240x320; HP iPAQ h6300)',
}

URLS=[
    '/',
    '/contact/',
    '/contact/results/',
    '/service-status/',
    '/weather/',
    '/desktop/',
    '/feature-suggestions/',
    '/feedback/',
    '/library/',
]

def verify_200(url, ua):
    try:
        request = urllib2.Request(url, headers={
            'User-Agent': ua,
        })
        file = urllib2.urlopen(url)
        if file.geturl() != url:
            # Redirected
            return file, 300
        else:
            return file, 200
    except urllib2.HTTPError, e:
        return None, e.code

def smoke_test(base_url):
    tests = 0
    status = 0
    print "MOLLY SMOKER"
    print "------------"
    
    for type, ua in USER_AGENTS.items():
        print
        print "Simulating", type
        for url in URLS:
            tests += 1
            file, code = verify_200(base_url + url, ua)
            if code != 200:
                status += 1
                print "FAIL", code, url
            else:
                print " OK ", code, url
    
    print "SUMMARY"
    print "-------"
    print
    print "Ran", tests, "tests"
    if status == 0:
        print "All passed - well done"
    else:
        print status, "tests failed"
    
    return status

if __name__ == '__main__':
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    sys.exit(smoke_test(base_url))