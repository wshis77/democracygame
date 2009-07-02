import datetime

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.core.paginator import InvalidPage
from django.core.paginator import EmptyPage

from django.db.models import Q
from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc

from emocracy.issues_content.models import IssueBody
from emocracy.voting.models import Issue
from emocracy.voting.models import Vote
from emocracy.profiles.models import UserProfile
from emocracy.gamelogic.models import MultiplyIssue

import gamelogic.actions

domain = Site.objects.get_current().domain

def paginate(request, qs):
    paginator = Paginator(qs, 3)  # TODO: add to settings.py
    try :
        pageno = int(request.GET.get('page', '1'))
    except ValueError:
        pageno = 1
    try :
        page = paginator.page(pageno)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages) #last page
    return page

class IssueVotesHandler(AnonymousBaseHandler):
    """Returns the vote count for an issue
       issue id should be provided
    """ 
    allowed_methods = ('GET',)
    fields = ('vote', 'vote_count',)
    model = Issue

    def read(self, request, id ,*args, **kwargs):
        try :
            issue = self.model.objects.get( id=id )
        except self.model.DoesNotExist :
            return rc.NOT_HERE
        
        votes = issue.vote_count()
        return votes

    @classmethod
    def vote(cls, vote):
        return vote[0]

    @classmethod
    def vote_count(cls, vote):
        return vote[1]

    @staticmethod
    def resource_uri():
        return ('api_issue_votes' , ['id'])
    

class VoteHandler(BaseHandler):
    """ returns the votes for an user. 
        makes it able to post to an user
    """
    allowed_methods = ('GET', 'POST' )
    fields = ('vote', 'time_stamp', 'issue_uri', 'keep_private', 'user_uri')
    model = Vote

    def read(self, request, *args, **kwargs):
        queryset = self.model.objects.filter( owner = request.user ).order_by('time_stamp')
        page = paginate(request, queryset)
        return page.object_list

    @classmethod
    def issue_uri(cls, vote):
        return "http://%s%s" % (domain , reverse('api_issue' , args=[vote.issue.id]))

    @classmethod
    def user_uri(cls, vote):
        return "http://%s%s" %(domain , reverse('api_user' , args=[vote.owner.id]))

    ## TODO use the @validate decorator of piston
    def create(self, request , issue=None , vote=None):
        attrs = { issue:issue , vote:vote }
        attrs.update(self.flatten_dict(request.POST))

        if self.exists(**attrs):
            return rc.DUPLICATE_ENTRY
        if not Issue.exists( id = attrs['issue']):
            return rc.BAD_REQUEST
        if not attrs.has_key('keep_private'):
            attrs['keep_private'] = False
        elif not ( attrs['keep_private'] == False or attrs['keep_private'] == True ):
            return rc.BAD_REQUEST 

        vote = gamelogic.actions.vote( 
                request.user , 
                Issue.objects.get(id=attrs['issue']),
                attrs['vote'],
                attrs['keep_private'],
                api_interface = "API" , # TODO add aplication interface!!
        )
        return vote

    @staticmethod
    def resource_uri():
        return ('api_vote' , ['issue' , 'vote'])
   

class AnonymousUserHandler(AnonymousBaseHandler):
    allowed_methods = ('GET',)
    fields = ('username', 'score', 'ranking' , 'user_uri')
    model = User

    def read(self, request, id=None, *args, **kwargs):
        queryset = self.model.objects.filter(id=id)
        page = paginate(request, queryset)
        return page.object_list

    @classmethod
    def score(cls, user):
        return user.get_profile().score

    @classmethod
    def user_uri(cls, user):
        return "http://%s%s" % (domain , reverse('api_user' , args=[user.id]))

    @classmethod
    def ranking(cls , user):
        p = user.get_profile()
        return UserProfile.objects.filter( score__gte = p.score ).count()

    @staticmethod
    def resource_uri():
        return ('api_user' , ['id'])


class UserHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('username', 'score', 'user_uri')
    anonymous = AnonymousUserHandler
    model = User

    def read(self, request, id=None, *args, **kwargs):
        if id:
            return self.model.objects.filter( id=id )
        else :
            queryset = self.model.objects.filter()
            page = paginate(request, queryset)
            return page.object_list

    @classmethod
    def score(cls, user):
        return user.get_profile().score

    @classmethod
    def user_uri(cls, user):
        return "http://%s%s" % (domain , reverse('api_user' , args=[user.id]))

    @staticmethod
    def resource_uri():
        return ('api_user' , ['id'])



class AnonymousIssueHandler(AnonymousBaseHandler):
    allowed_methods = ('GET',)
    fields = ('issue_uri', 'title', 'body', ('owner', ('username', 'user_uri',)), 'time_stamp', 'source_type', 'url')
    model = IssueBody

    def read(self, request, id=None , *args, **kwargs):
        if id:
            return self.model.objects.filter( id=id )
        else :
            queryset = self.model.objects.order_by( '-time_stamp' )
            page = paginate(request, queryset)
            return page.object_list

        queryset = self.model.objects.filter()
        page = paginate(request, queryset)
        return page.object_list

    @classmethod
    def user_uri(cls, issue):
        return "http://%s%s" % (domain , reverse('api_user' , args=[issue.owner]))

    @classmethod
    def issue_uri(cls, issue):
        return "http://%s%s" % (domain , reverse('api_issue' , args=[issue.id]))

    @staticmethod
    def resource_uri():
        return ('api_issue' , ['id'])


class IssueHandler(BaseHandler):
    allowed_methods = ('POST',)
    anonymous = AnonymousIssueHandler
    fields = ('issue_uri', 'title', 'body', ('owner', ('username', 'user_uri',)), 'time_stamp', 'souce_type', 'url')
    model = IssueBody

    def create(self, request):
        attrs = self.flatten_dict(request.POST)

        if self.exists(**attrs):
            return rc.DUPLICATE_ENTRY
        else :
            issue = gamelogic.actions.propose(
                request.user,
                attrs['title'],
                attrs['body'],
                attrs['owners_vote'],
                attrs['url'],
                attrs['source_type'],
                attrs['is_draft'],
                None,
            )
            if issue : return issue
            else : rc.BAD_REQUEST

    def read(self, request, id=None):
        self.anonymous.read(self,request , id)

    @classmethod
    def user_uri(cls, issue):
        self.anonymous.user_uri(cls , issue)

    @classmethod
    def issue_uri(cls, issue):
        self.anonymous.issue_uri( cls , issue )

    @staticmethod
    def resource_uri():
        return ('api_issue' , ['id'])


class AnonymousMultiplyHandler( AnonymousBaseHandler ):
    allowed_methods = ('GET',)
    model = MultiplyIssue
    fields = ('user' , 'time_stamp' , 'issue' , 'downgrade' , )

    def read(self, request, id=None , *args, **kwargs):
        """ Read the active multiplies for specific issue
            or all multiplies in decending paginated order
        """
        if id:
            return self.model.objects.filter( issue=id )
        else :
            queryset = self.model.objects.order_by( '-time_stamp' )
            page = paginate(request, queryset)
            return page.object_list

        queryset = self.model.objects.filter()
        page = paginate(request, queryset)
        return page.object_list

class MultiplyHandler( BaseHandler ):
    """ If a user has enough game points the user can multiply the value
        of an issue.
    """
    allower_methods = ('GET' , 'POST')
    anonymous = AnonymousMultiplyHandler
    model = MultiplyIssue
    fields = ('user' , 'time_stamp' , 'issue' , 'downgrade' , )

    def read(self, request, id=None , *args, **kwargs):
        return self.anonymous.read( self , request , id , *args , **kwargs )

    def create( self , request ):
        """ expects an issue id and optional a downgrade boolean
            in the POST data
        """
        attrs = self.flatten_dict(request.POST)

        if self.exists(**attrs):
            return rc.DUPLICATE_ENTRY
        else :
            issue = gamelogic.actions.multiply(
                request.user,
                attrs['issue'],
                attrs.get('downgrade', False) ,
            )
            if issue : return issue
            else : return rc.BAD_REQUEST

    @staticmethod
    def resource_uri():
        return ('api_multiply' , ['id'])



