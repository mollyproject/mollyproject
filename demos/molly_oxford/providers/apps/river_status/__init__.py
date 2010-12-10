import random, urllib2

from lxml import etree

from molly.conf.settings import batch

from molly_oxford.apps.river_status.models import FlagStatus

class RiverStatusProvider(object):
    _OURCS_URL = "http://www.ourcs.org.uk/disclaimer"

    @batch('%(min)d,1%(min)d,2%(min)d,3%(min)d,4%(min)d,5%(min)d * * * *' % {'min': random.randint(0, 9)})
    def import_data(self, metadata, output):

        xml = etree.parse(urllib2.urlopen(self._OURCS_URL), parser=etree.HTMLParser())
        tbody = xml.getroot().find(".//div[@id='sidebar']/table")

        for i, tr in enumerate(tbody.findall('tr')):
            name = tr[0].text.split(':')[0]

            status = tr[1][0].attrib['src'][:-4].split('_')[-1]

            try:
                flag_status = FlagStatus.objects.get(order=i)
            except FlagStatus.DoesNotExist:
                flag_status = FlagStatus(order=i)

            flag_status.name = name

            flag_status.status = status

            flag_status.save()

        FlagStatus.objects.filter(order__gt = i).delete()
