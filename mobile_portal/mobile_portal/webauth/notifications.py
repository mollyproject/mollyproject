from alexdutton.nightline.notifications import Notification, register_notification

class WebauthFailureNotification(Notification):
    """Sent to the IT Officer to inform them that the site was unable to contact the OU Webauth server."""
    name = 'Auth/WebauthFailure'
    perm_to_edit = 'base.is_it_officer'
    allow_defer = True
    
    def get_recipients(self):
        return 'IT Officer'
register_notification(WebauthFailureNotification)