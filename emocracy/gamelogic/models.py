import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.signals import post_save 

from emocracy.issues_content.models import IssueBody
from emocracy.voting.models import Issue
from emocracy.profile.models import UserProfile
from levels import update_level

tag_count_threshold = 10

post_save.connect(update_level , sender=UserProfile)

roles = [u"anonymous citizen", u"citizen", u"active citizen", u"opinion leader", u"candidate", u"parliament member", u"minister", u'prime minister']

class OpinionLeaderMultiply(models.Model):
    user = models.ForeignKey(User, unique = True)
    time_stamp = models.DateTimeField(auto_now_add = True)
    issue = models.ForeignKey( Issue )

    def __unicode__(self):
        return _(u'%(user)s  multiplies for %(issue)s' % {
            'user' : self.user.username,
            'issue' : self.issue.title, 
            }) 
