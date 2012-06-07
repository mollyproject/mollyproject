import unittest2
import mock
from datetime import date, time

from molly.apps.places.providers.metoffice import MetOfficeProvider


class MetOfficeObservationsProviderTest(unittest2.TestCase):
    """
    Tests for MetOffice/Observations provider
    """

    def test_scrape_xml(self):
        with open('molly/apps/weather/tests/data/metoffice_observations.xml') as f:
            content = f.read()
            f.close()

        provider = MetOfficeProvider('test')
        observations = provider.scrape_xml(content)

        # 2011-11-22Z <Rep W="104" V="MO" T="10.3" S="5" P="1023" G="-99" D="NW">1200</Rep>
        obs_date = date(day=22, month=11, year=2011)
        obs_time = time(1200)
        obs_weather_type = 104
        obs_visibility = 'MO'
        obs_temperature = 10.3
        obs_wind_speed = 5
        obs_pressure = 1023
        obs_wind_gust = -99
        obs_wind_direction = 'NW'

        break
