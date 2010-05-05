from django.http import HttpResponseRedirect

class HttpResponseSeeOther(HttpResponseRedirect):
    status_code = 303
