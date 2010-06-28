from django.db import models

FLAG_STATUS_CHOICES = (
    ('green', 'Green: No restrictions'),
    ('blue', 'Blue: No novice coxes'),
    ('yellow', 'Yellow: Senior crews only'),
    ('red', 'Red: No crews allowed out'),
    ('grey', 'Grey: Flag not currently being maintained'),
)

class FlagStatus(models.Model):
    order = models.IntegerField()
    name = models.TextField()
    status = models.CharField(max_length=6, choices=FLAG_STATUS_CHOICES)

    def get_icon_url(self):
        return "http://www.ourcs.org.uk/files/image/icons/flag_%s.png" % self.status
