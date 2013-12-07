from datetime import datetime
import socket
import xmlrpclib

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.utils.translation import ugettext_lazy as _


class PingedURLManager(models.Manager):
    def process_pending(self):
        for item in self.filter(status=self.model.PENDING).select_related(
                'server'):
            try:
                rpc = xmlrpclib.Server(item.server.url)
                reply = rpc.weblogUpdates.ping(
                    item.weblogname,
                    item.weblogurl,
                    item.changesurl or item.weblogurl)
                item.status = (
                    self.model.FAILED if reply['flerror']
                    else self.model.SUCCESSFUL)
                item.message = reply['message']
            except socket.error as exc:
                item.status = self.model.ERROR
                item.message = u'Socket error: %s' % (repr(exc),)
            except xmlrpclib.ProtocolError as exc:
                item.status = self.model.ERROR
                item.message = u'Protocol error: %s, %s, %s' % (
                    exc.errcode, exc.errmsg, exc.url)
            except xmlrpclib.Fault as exc:
                item.status = self.model.ERROR
                item.message = exc.faultString
            except Exception as exc:
                item.status = self.model.ERROR
                item.message = u'Unknown error: %s' % (repr(exc),)

            item.save()

    def for_object(self, obj):
        return self.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk)

    def create_for_servers(self, **kwargs):
        for server in PingServer.objects.all():
            self.create(server=server, **kwargs)


class PingServer(models.Model):
    url = models.URLField(_('url'), verify_exists=False)

    def __unicode__(self):
        return self.url

    def delete(self):
        self.pingedurl_set.all().delete()
        super(PingServer, self).delete()


class PingedURL(models.Model):
    PENDING = 1
    FAILED = 2
    SUCCESSFUL = 3
    ERROR = 4

    STATUS_CHOICES = (
        (PENDING, _('pending')),
        (FAILED, _('failed')),
        (SUCCESSFUL, _('successful')),
        (ERROR, _('error')),
    )

    created = models.DateTimeField(_('created'), default=datetime.now)
    server = models.ForeignKey(PingServer)

    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey()

    weblogname = models.CharField(_('weblog name'), max_length=200)
    weblogurl = models.CharField(_('weblog URL'), max_length=200)
    changesurl = models.CharField(
        _('changes URL'), max_length=200, blank=True, default=u'')

    status = models.IntegerField(
        _('status'), choices=STATUS_CHOICES, default=PENDING)
    message = models.CharField(
        _('message'), max_length=200, blank=True, default=u'')

    objects = PingedURLManager()

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return self.changesurl or self.weblogurl
