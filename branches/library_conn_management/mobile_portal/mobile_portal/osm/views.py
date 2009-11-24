import pytz
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from models import GeneratedMap

def generated_map(request, hash):
    gm = get_object_or_404(GeneratedMap, hash=hash)
    response = HttpResponse(open(gm.get_filename(), 'r').read(), mimetype='image/png') 
    last_updated = pytz.utc.localize(gm.generated)
    
    response['ETag'] = hash
    return response