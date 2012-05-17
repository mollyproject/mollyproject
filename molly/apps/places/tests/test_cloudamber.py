import unittest
from django.test.utils import setup_test_environment
setup_test_environment()

from transports import CloudAmberBusRtiProvider

class CloudAmberBusRtiProviderTest(unittest.TestCase):

    def test_info(self):
        """
        Test case covering stop's services and departure times
        """

        # HTML retrived from http://oxontime.voyagertest.com/Naptan.aspx?t=departure&sa=69327545&dc=&ac=96&vc=&x=0&y=0&format=xhtml
        with open('data/cloudamber-info.html') as f:
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

        provider = CloudAmberBusRtiProvider()
        services, messages = provider.parse_html(content)

        self.assertEqual(messages, '')

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
        with open('data/cloudamber-messages.html') as f:
            content = f.read()
            f.close()

        message = '-The terminus for the inbound S1 is at stop B1 (west end of George St) <br/> -For the S2 & S3 go to Gloucester Green (bus station) <br/> -Stop closed - long term closure to allow demolition & rebuilding works <br/> -Please refer to notices posted at the stop'

        provider = CloudAmberBusRtiProvider()
        services, messages = provider.parse_html(content)
        self.assertEqual(messages, message)


if __name__ == "__main__":
    unittest.main()
