/* Tests for the home UI renderer */
module("molly.ui.bootstrap.home")

var fixture_home_response = {
    "messages": [],
    "applications": [
        {
            "application_name": "molly.apps.home",
            "url": "/",
            "local_name": "home",
            "display_to_user": false,
            "title": "Home"
        },
        {
            "title": "Places",
            "url": "/places/",
            "accesskey": 1,
            "display_to_user": true,
            "local_name": "places",
            "application_name": "molly.apps.places"
        },
        {
            "title": "Transport",
            "url": "/transport/",
            "accesskey": 2,
            "display_to_user": true,
            "local_name": "transport",
            "application_name": "molly.apps.transport"
        },
        {
            "title": "Podcasts",
            "url": "/podcasts/",
            "accesskey": 3,
            "display_to_user": true,
            "local_name": "podcasts",
            "application_name": "molly.apps.podcasts"
        },
        {
            "title": "Webcams",
            "url": "/webcams/",
            "accesskey": 4,
            "display_to_user": true,
            "local_name": "webcams",
            "application_name": "molly.apps.webcams"
        },
        {
            "title": "Weather",
            "url": "/weather/",
            "accesskey": 5,
            "display_to_user": true,
            "local_name": "weather",
            "application_name": "molly.apps.weather"
        },
        {
            "application_name": "molly.apps.search",
            "url": "/search/",
            "local_name": "search",
            "display_to_user": false,
            "title": "Search"
        },
        {
            "application_name": "molly.apps.feeds",
            "url": null,
            "local_name": "feeds",
            "display_to_user": false,
            "title": "Feeds"
        },
        {
            "title": "News",
            "url": "/news/",
            "accesskey": 6,
            "display_to_user": true,
            "local_name": "news",
            "application_name": "molly.apps.feeds.news"
        },
        {
            "title": "Events",
            "url": "/events/",
            "accesskey": 7,
            "display_to_user": true,
            "local_name": "events",
            "application_name": "molly.apps.feeds.events"
        },
        {
            "application_name": "molly.maps",
            "url": "/maps/",
            "local_name": "maps",
            "display_to_user": false,
            "title": "Maps"
        },
        {
            "application_name": "molly.geolocation",
            "url": "/geolocation/",
            "local_name": "geolocation",
            "display_to_user": false,
            "title": "Geolocation"
        },
        {
            "application_name": "molly.apps.feedback",
            "url": "/feedback/",
            "local_name": "feedback",
            "display_to_user": false,
            "title": "Feedback"
        },
        {
            "application_name": "molly.external_media",
            "url": "/external-media/",
            "local_name": "external-media",
            "display_to_user": false,
            "title": "External Media"
        },
        {
            "application_name": "molly.wurfl",
            "url": "/device-detection/",
            "local_name": "device-detection",
            "display_to_user": false,
            "title": "Device detection"
        },
        {
            "application_name": "molly.url_shortener",
            "url": "/url-shortener/",
            "local_name": "url-shortener",
            "display_to_user": false,
            "title": "URL Shortener"
        },
        {
            "application_name": "molly.utils",
            "url": null,
            "local_name": "utils",
            "display_to_user": false,
            "title": "Molly utility services"
        },
        {
            "application_name": "molly.apps.feature_vote",
            "url": "/feature-suggestions/",
            "local_name": "feature-suggestions",
            "display_to_user": false,
            "title": "Feature suggestions"
        },
        {
            "application_name": "molly.favourites",
            "url": "/favourites/",
            "local_name": "favourites",
            "display_to_user": false,
            "title": "Favourite pages"
        },
        {
            "application_name": "molly.routing",
            "url": null,
            "local_name": "routing",
            "display_to_user": false,
            "title": "Routing"
        },
        {
            "application_name": "molly.routing",
            "url": null,
            "local_name": "routing",
            "display_to_user": false,
            "title": "Routing"
        }
    ],
    "view_name": "home:index",
    "hide_feedback_link": true,
    "weather": {
        "outlook": null,
        "wind_direction": null,
        "ptype": "o",
        "uv_risk": null,
        "location_id": "bbc/9",
        "id": 1,
        "sunrise": null,
        "modified_date": "2012-04-07 17:13:03.351162",
        "temperature": null,
        "_pk": 1,
        "location": [
            53.333,
            -2.15
        ],
        "pk": 1,
        "min_temperature": null,
        "max_temperature": null,
        "observed_date": "2012-04-07 16:00:00",
        "_type": "molly.apps.weather.Weather",
        "visibility": null,
        "pressure": null,
        "icon": "dunno",
        "wind_speed": null,
        "name": "Manchester, United Kingdom",
        "humidity": null,
        "sunset": null,
        "pressure_state": null,
        "published_date": "2012-04-07 16:50:00",
        "pollution": null
    },
    "favourites": []
}

function triggerSuccessfulHomeIndexRender() {
    var test_view = new HomeIndexView();
    test_view.handle_success(fixture_home_response);
}

test("correct number of apps are rendered", function() {
    triggerSuccessfulHomeIndexRender();
    equal(7, $('#body .row-fluid .app').length);
})

test("apps are partitioned into rows of 6", function() {
    triggerSuccessfulHomeIndexRender();
    equal(6, $('#body .row-fluid:first').find('.app').length);
    equal(1, $('#body .row-fluid:nth-child(2)').find('.app').length);
})

test("apps are set to span 2", function() {
    triggerSuccessfulHomeIndexRender();
    equal(7, $('#body .row-fluid .app.span2').length);
})

test("apps contain their item name", function() {
    triggerSuccessfulHomeIndexRender();
    equal("Places", $('#body .app:first span.app-title').text());
})

test("apps have their local name as class", function() {
    triggerSuccessfulHomeIndexRender();
    ok($('#body .app:first').hasClass('app-places'));
})

test("loading clears the canvas before rendering", function() {
    $('#body').append($('<div/>').addClass('junk'));
    triggerSuccessfulHomeIndexRender();
    equal(0, $('.junk').length);
})
