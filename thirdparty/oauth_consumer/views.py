# Create your views here.
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from oauth_consumer import EmoOAuthConsumerApp

emoauth = EmoOAuthConsumerApp()

@emoauth.require_access_token
def index(request):
    return HttpResponseRedirect("http://tp.buhrer.net:8080/")
    
