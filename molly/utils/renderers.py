from django.template import RequestContext
from django.shortcuts import render_to_response


def mobile_render(request, context, template, headers={}, status=200):
    return render_to_response(template+'.xhtml', context, context_instance=RequestContext(request))
