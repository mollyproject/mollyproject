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
    '/contact/',
    '/contact/results/',
    '/contact/results/?query=northwood',
    '/desktop/',
    '/feature-suggestions/',
    '/feature-suggestions/1/',
    '/feedback/',
    '/news/',
    '/news/molly/',
    '/news/molly/272/',
    '/',
    '/about/',
    '/messages/',
    '/library/',
    '/library/search/',
    '/library/search/?title=erewhon&author=&isbn=',
    '/library/item:701036753/',
    '/library/item:701036753/NLS:0Hall/',
    '/places/',
    #'/places/nearby/',
    #'/places/nearby/bus-stop/',
    '/places/category/',
    '/places/category/unit/',
    '/places/atco:9100OXFD/',
    '/places/atco:9100OXFD/?board=arrivals',
    '/places/atco:9100OXFD/nearby/',
    '/places/atco:9100OXFD/nearby/bus-stop/',
    '/places/osm:N295953659/update/',
    '/places/atco:340001903OUT/service?route=S5',
    '/places/openstreetmap/',
    #'/places/api/',
    '/podcasts/',
    '/podcasts/category:bbc-radio-1/',
    '/podcasts/radio1/moyles/',
    #'/podcasts/itunesu_redirect/',
    '/search/',
    '/search/?query=molly+project',
    '/service-status/',
    '/transport/bus/',
    '/transport/rail/',
    '/transport/park-and-ride/',
    '/weather/',
    '/webcams/',
    '/webcams/york-minster/',
    '/auth/',
    '/auth/clear-session/',
    '/favourites/',
    '/geolocation/',
    #'/geolocation/clear/',
    #'/geolocation/favourites/',
    '/maps/touchmaplite/',
    '/maps/osm/about/',
    '/maps/osm/gpx/foo/',
    '/url-shortener/?path=/',
    '/device-detection/',
    '/weblearn/',
    '/weblearn/?force_login',
]

def verify_200(url, ua):
    try:
        request = urllib2.Request(url, headers={
            'User-Agent': ua,
        })
        file = urllib2.urlopen(url)
        if file.geturl() != url:
            # Redirected
            file2 = urllib2.urlopen(file.geturl())
            if file2.geturl() != file.geturl():
                # still redirected, let's assume it's
                # not a normal behaviour?
                return file2, 300
            else:
                return file2, 200
            # avoid infinite loop
            #return verify_200(file.geturl(), ua)
        else:
            return file, 200
    except urllib2.HTTPError, e:
        return None, e.code

def smoke_test(base_url):
    tests = 0
    status = 0
    print "MOLLY SMOKER %s" % base_url
    print "------------"

    for type, ua in USER_AGENTS.items():
        print
        print "Simulating", type
        for url in URLS:
            tests += 1
            file, code = verify_200(base_url + url, ua)
            if code == 404:
                print "SKIP", url
            elif code != 200:
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

def command(base_url='http://localhost:8000'):
    sys.exit(smoke_test(base_url))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command(base_url=sys.argv[1])
    else:
        command()
