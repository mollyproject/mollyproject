"""
The CIF standard is documented at
http://www.atoc.org/clientfiles/File/RSPDocuments/20070801.pdf and is a file
format created by (and used by) Network Rail to expose rail timetables. It is
only used for UK rail timetables.

It is dissimilar, but related to, the ATCO-CIF standard
"""

from datetime import date, time, timedelta
from string import capwords

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, reset_queries
from django.utils.translation import ugettext_noop as _

from molly.apps.places.models import (Entity, EntityType, EntityTypeCategory,
                                      Source, Route, Journey, ScheduledStop)
from molly.apps.places.providers import BaseMapsProvider
from molly.conf.provider import task


class CifTimetableProvider(BaseMapsProvider):

    def __init__(self,
                 entity_manager=Entity.objects,
                 entity_type_manager=EntityType.objects,
                 entity_type_category_manager=EntityTypeCategory.objects,
                 source_manager=Source.objects,
                 route_manager=Route.objects,
                 journey_manager=Journey.objects,
                 scheduled_stop_manager=ScheduledStop.objects,
                 filename=None):
        self._entity_manager = entity_manager
        self._entity_type_manager = entity_type_manager
        self._entity_type_category_manager = entity_type_category_manager
        self._source_manager = source_manager
        self._route_manager = route_manager
        self._journey_manager = journey_manager
        self._scheduled_stop_manager = scheduled_stop_manager
        self._tiplocs = {}
        self._routes = {}
        self._filename = filename

    def _parse_tiploc(self, line):
        tiploc = line[2:9].strip()
        entities = self._entity_manager.get_entity("tiploc", tiploc)
        try:
            entity = entities[0]
        except ObjectDoesNotExist:
            entity = self._entity_manager.create(
                source=self.source,
                primary_type=self.entity_type,
                identifiers={'tiploc': tiploc},
                titles={'en': capwords(line[18:44].strip())}
            )
        self._tiplocs[tiploc] = entity

    def save_journey(self):
        pass

    def _parse_cif_date(self, cifdate):
        y = int(cifdate[:2])
        m = int(cifdate[2:4])
        d = int(cifdate[4:])
        if y < 60:
            y += 2000
        else:
            y += 1900
        return date(y, m, d)

    def _parse_cif_time(self, ciftime):
        if ciftime.strip() == '':
            return None
        h = int(ciftime[:2])
        m = int(ciftime[2:4])
        s = 30 if ciftime[4] == 'H' else 0
        return time(h, m, s)

    def _parse_basic_schedule(self, line):
        if hasattr(self, '_current_journey'):
            reset_queries()
            with transaction.commit_on_success():
                self._save_stops(self._save_journey(self._save_route()))

        self._current_journey = {
            'external_ref': line[3:9],
            'runs_from': self._parse_cif_date(line[9:15]),
            'runs_until': self._parse_cif_date(line[15:21]),
            'runs_on_monday': line[21] == '1',
            'runs_on_tuesday': line[22] == '1',
            'runs_on_wednesday': line[23] == '1',
            'runs_on_thursday': line[24] == '1',
            'runs_on_friday': line[25] == '1',
            'runs_on_saturday': line[26] == '1',
            'runs_on_sunday': line[27] == '1',
            'runs_in_termtime': True,
            'runs_on_bank_holidays': line[28] not in ('X', 'E', 'G'),
            'runs_on_non_bank_holidays': True,
            # TODO: Extract category/class/catering for more information here
            'vehicle': 'TRAIN'
        }
        self._current_route = {
            'external_ref': line[3:9],
            'service_id': line[32:36]
        }
        self._stops = []

    def _parse_extended_schedule(self, line):
        # TODO: Map to full name
        self._current_route['operator'] = line[11:13]

    def _parse_origin(self, line):
        self._stops.append({
            'entity': self._tiplocs[line[2:9].strip()],
            'std': self._parse_cif_time(line[10:15]),
            'activity': 'O'
        })

    def _parse_intermediate(self, line):
        sta = self._parse_cif_time(line[10:15])
        std = self._parse_cif_time(line[15:20])
        if sta is None and std is None:
            std = self._parse_cif_time(line[20:25])
            activity = 'N'
        else:
            for i in range(42, 54, 2):
                activity = {
                    'D': 'D',
                    'T': 'B',
                    'U': 'P',
                }.get(line[i:i + 2].strip())
                if activity is not None:
                    break
            else:
                activity = 'N'
        self._stops.append({
            'entity': self._tiplocs[line[2:9].strip()],
            'sta': sta,
            'std': std,
            'activity': activity,
            'times_estimated': False
        })

    def _parse_terminate(self, line):
        self._stops.append({
            'entity': self._tiplocs[line[2:9].strip()],
            'sta': self._parse_cif_time(line[10:15]),
            'activity': 'F'
        })

    def _save_route(self):
        route, created = self._route_manager.get_or_create(
            external_ref=self._current_route['external_ref'],
            defaults=self._current_route
        )
        if not created:
            for key, value in self._current_route.items():
                setattr(route, key, value)
            route.save()
        return route

    def _save_journey(self, route):
        self._current_journey['route'] = route
        journey, created = self._journey_manager.get_or_create(
            external_ref=self._current_journey['external_ref'],
            defaults=self._current_journey
        )
        if not created:
            for key, value in self._current_journey.items():
                setattr(journey, key, value)
            journey.save()
        return journey

    def _save_stops(self, journey):
        journey.scheduledstop_set.all().delete()
        for order, stop in enumerate(self._stops):
            stop['journey'] = journey
            stop['order'] = order
            self._scheduled_stop_manager.create(**stop)

    def import_from_string(self, cif):
        # TODO: changes en route
        for line in cif.split('\n'):
            self._handle_line(line)
        if hasattr(self, '_current_journey'):
            with transaction.commit_on_success():
                self._save_stops(self._save_journey(self._save_route()))

    @task(run_every=timedelta(days=7))
    def import_from_file(self, **metadata):
        with open(self._filename) as file:
            for line in file:
                self._handle_line(line)
        if hasattr(self, '_current_journey'):
            with transaction.commit_on_success():
                self._save_stops(self._save_journey(self._save_route()))

    def _handle_line(self, line):
        if line[:2] == "TI":
            self._parse_tiploc(line)
        elif line[:2] == 'BS':
            self._parse_basic_schedule(line)
        elif line[:2] == 'BX':
            self._parse_extended_schedule(line)
        elif line[:2] == 'LO':
            self._parse_origin(line)
        elif line[:2] == 'LI':
            self._parse_intermediate(line)
        elif line[:2] == 'LT':
            self._parse_terminate(line)

    @property
    def source(self):
        if not hasattr(self, '_source'):
            self._source = self._source_manager.get_or_create(
                module_name=__name__,
                defaults={'name': 'CIF Timetable Provider'}
            )[0]
        return self._source

    @property
    def entity_type(self):
        if not hasattr(self, '_entity_type'):
            category = self._entity_type_category_manager.get_or_create(
                name=_('Transport'))[0]
            self._entity_type = self._entity_type_manager.get_or_create(
                slug='rail-timing-point',
                category=category,
                defaults={
                    'verbose_names': {
                        'en': ('rail network timing point',
                               'a rail network timing point',
                               'rail network timing points')
                    }
                }
            )[0]
        return self._entity_type
