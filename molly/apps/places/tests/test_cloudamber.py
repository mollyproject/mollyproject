import unittest2
import mock

from molly.apps.places.providers.cloudamber import CloudAmberBusRtiProvider, CloudAmberBusRouteProvider, Route, StopOnRoute


class CloudAmberBusRouteProviderTest(unittest2.TestCase):
    """Simple tests which asssert the correct numbers of Routes and StopOnRoute
    objects are being created from a stored data.
    """
    def test_scrape_search(self):
        provider = CloudAmberBusRouteProvider('foo')
        provider.url = 'molly/apps/places/tests/data/cloudamber-search.html'
        provider._scrape_route = mock.Mock()
        Route.objects.get_or_create = mock.Mock(return_value=[mock.Mock(), True])
        provider._scrape_search()
        # Attempts to create 200 routes
        self.assertEqual(Route.objects.get_or_create.call_count, 201)

    def test_scrape_route(self):
        provider = CloudAmberBusRouteProvider('foo')
        provider._get_entity = mock.Mock(return_value='bar')
        StopOnRoute.objects.create = mock.Mock()
        provider._scrape_route(6, 'molly/apps/places/tests/data/cloudamber-route.html')
        self.assertEqual(StopOnRoute.objects.create.call_count, 18)

class CloudAmberBusRtiProviderTest(unittest2.TestCase):

    def test_info(self):
        """
        Test case covering stop's services and departure times
        """

        # HTML retrived from http://oxontime.voyagertest.com/Naptan.aspx?t=departure&sa=69327545&dc=&ac=96&vc=&x=0&y=0&format=xhtml
        with open('molly/apps/places/tests/data/cloudamber-info.html') as f:
            content = f.read()
            f.close()
       
        # What we are testing
        sms_number = 69327545
        stop_name = 'George Street B1'
        first_stop_service_number = '14A'
        first_stop_destination = 'JR Hospital'
        first_stop_departure_time = 'DUE'
        first_stop_next_departure_time = '3 mins'
        #first_stop_operator = 'SOX'
        last_stop_service_number = '17'
        last_stop_destination = 'Cutteslowe'
        last_stop_departure_time = '41 mins'
        #last_stop_operator = 'SOX'

        provider = CloudAmberBusRtiProvider('foo.bar')
        services, messages = provider.parse_html(content)

        self.assertEqual(messages, [])

        # first service (NOT BUS) expected at the bus stop
        first = services[0]
        self.assertEqual(first.get('service'), first_stop_service_number)
        self.assertEqual(first.get('destination'), first_stop_destination)
        self.assertEqual(first.get('next'), first_stop_departure_time)
        self.assertEqual(first.get('following')[0], first_stop_next_departure_time)

        # last service (NOT BUS) expected at the bus stop
        last = services[-1]
        self.assertEqual(last.get('service'), last_stop_service_number)
        self.assertEqual(last.get('destination'), last_stop_destination)
        self.assertEqual(last.get('next'), last_stop_departure_time)

    def test_messages(self):
        """
        Test case covering messages added to a bus stop
        """

        # HTML retrieved from http://oxontime.voyagertest.com/Naptan.aspx?t=departure&sa=69327545&dc=&ac=96&vc=&x=0&y=0&format=xhtml
        with open('molly/apps/places/tests/data/cloudamber-messages.html') as f:
            content = f.read()
            f.close()

        message = '-The terminus for the inbound S1 is at stop B1 (west end of George St) <br/> -For the S2 & S3 go to Gloucester Green (bus station) <br/> -Stop closed - long term closure to allow demolition & rebuilding works <br/> -Please refer to notices posted at the stop'

        provider = CloudAmberBusRtiProvider('foo.bar')
        services, messages = provider.parse_html(content)
        self.assertEqual(messages[0], message)


if __name__ == "__main__":
    unittest2.main()
