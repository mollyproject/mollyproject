from django.db import models

class Idea(models.Model):
    user_name = models.TextField()
    user_email = models.EmailField()

    title = models.TextField()
    description = models.TextField()

    up_vote = models.IntegerField(default=0)
    down_vote = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    last_commented = models.DateTimeField(null=True)

    class Meta:
        ordering = ('-last_commented', '-created')

    @property
    def net_votes(self):
        return self.up_vote - self.down_vote

