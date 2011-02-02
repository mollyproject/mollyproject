import re

from molly.apps.podcasts.providers import OPMLPodcastsProvider as MollyOPML

class OPMLPodcastsProvider(MollyOPML):
    
    def extract_medium(self, url):
        # There are four podcast feed relics that existed before the
        # -audio / -video convention was enforced. These need to be
        # hard-coded as being audio feeds.
        match_groups = self.rss_re.match(url).groups()
        medium = {
            'engfac/podcasts-medieval': 'audio',
            'oucs/ww1-podcasts': 'audio',
            'philfac/uehiro-podcasts': 'audio',
            'offices/undergrad-podcasts': 'audio',
        }.get(self.extract_slug(url), match_groups[1])
        return medium
    
    def decode_category(self, attrib):
        category = attrib['category']
        category = dict(self.CATEGORY_RE.match(s).groups() for s in category.split(','))
        slug, name = category['division_code'], category['division_name']
        name = urllib.unquote(name.replace('+', ' '))

        podcast_category, created = PodcastCategory.objects.get_or_create(slug=slug,name=name)

        try:
            podcast_category.order = self.CATEGORY_ORDERS[slug]
        except KeyError:
            self.CATEGORY_ORDERS[slug] = len(self.CATEGORY_ORDERS)
            podcast_category.order = self.CATEGORY_ORDERS[slug]

        podcast_category.save()
        return podcast_category

