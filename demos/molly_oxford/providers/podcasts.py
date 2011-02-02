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

