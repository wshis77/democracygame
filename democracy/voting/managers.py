from django.db import models, IntegrityError
from django.db import connection
from django.db.models import Avg, Count

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext as _


votes = {
    -1 : _(u"Against"),
    1  : _(u"For"),
}
blank_votes = {
    # content related problems with issues:
    10 : _(u'Unconvincing'),
    11 : _(u'Not political'),
    12 : _(u'Can\'t completely agree'),
    # form related problems with issues":
    13 : _(u"Needs more work"),
    14 : _(u"Badly worded"),
    15 : _(u"Duplicate"),
    16 : _(u'Unrelated source'),
    # personal considerations:
    17 : _(u'I need to know more'),
    18 : _(u'Ask me later'),
    19 : _(u'Too personal'),
}
possible_votes = votes
possible_votes.update(blank_votes)


class VoteManager(models.Manager):

    def get_for_object(self, obj):
        """
        Get queryset for votes on object
        """
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type = ctype.pk,
            object_id = obj.pk)

    def get_user_votes(self, user):
        """
        Get queryset for active votes by user
        """
        return Vote.objects.filter(owner=user, is_archived=False).order_by("time_stamp").reverse()
    
    def get_object_votes(self, obj, all=False):
        """
        Get a dictionary mapping vote to votecount
        """
        object_id = obj._get_pk_val()
        ctype = ContentType.objects.get_for_model(obj)
        queryset = self.filter(content_type=ctype, object_id=object_id)
    
        if not all:
            queryset = queryset.filter(is_archived=False) # only pick active votes

        queryset = queryset.values('vote')
        queryset = queryset.annotate(vcount=Count("vote")).order_by()

        votes = {}

        for count in queryset:
            votes[count['vote']] = count['vcount']

        return votes

    def get_objects_votes(self, objects, all=False):
        """
        Get a dictinary mapping objects ids to dictinary which maps direction to votecount
        """
        object_ids = [o._get_pk_val() for o in objects]
        if not object_ids:
            return {}
        object_ids.reverse()
        ctype = ContentType.objects.get_for_model(objects[0])
        queryset = self.filter(content_type=ctype, object_id__in=object_ids)

        if not all:
            queryset = queryset.filter(is_archived=False) # only pick active votes
        queryset = queryset.values('object_id', 'vote',)
        queryset = queryset.annotate(vcount=Count("vote")).order_by()
       
        vote_dict = {}
        for votecount  in queryset:
            object_id = votecount['object_id']
            votes = vote_dict.setdefault(object_id , {})
            votes[votecount['vote']] =  votecount['vcount']

        return vote_dict

    def record_vote(self, user, obj, direction , api_interface=None ):
        """
        Archive old votes by switching the is_archived flag to True
        for all the previous votes on <obj> by <user>.
        And we check for and dismiss a repeated vote.
        We save old votes for research, probable interesting
        opinion changes.
        """
        if not direction in possible_votes.keys():
            raise ValueError('Invalid vote %s must be in %s' % (direction , possible_votes.keys()))

        ctype = ContentType.objects.get_for_model(obj)
        votes = self.filter(user=user, content_type=ctype, object_id=obj._get_pk_val(), is_archived=False)

        voted_already = False
        repeated_vote = False
        if votes:
            voted_already = True
            for v in votes:
                if direction == v.vote: #check if you do the same vote again.
                    repeated_vote = True
                else:
                    v.is_archived = True
                    v.save()            
        vote = None
        if not repeated_vote:
            vote = self.create( user=user , content_type=ctype,
                         object_id=obj._get_pk_val(), vote=direction,
                         api_interface=api_interface , is_archived=False 
                        )
            vote.save()
        return repeated_vote, voted_already, vote
