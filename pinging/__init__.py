from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import signals
from django.utils.functional import curry

from pinging.models import PingedURL


def register(model, **kwargs):
    """
    Example::

        pinging.register(
            YourModel, weblogname='something', weblogurl='somethingelse')
    """

    if not all(hasattr(settings, key) for key in (
            'PINGING_WEBLOG_NAME', 'PINGING_WEBLOG_URL')):
        raise ImproperlyConfigured(
            'You have to specify PINGING_WEBLOG_NAME '
            'and PINGING_WEBLOG_URL to be able to use ``pinging.register``,')

    # reference must not be weak because the receiver is dynamically
    # constructed here
    signals.post_save.connect(
        curry(post_save_handler, **kwargs),
        sender=model,
        weak=False)


def post_save_handler(signal, sender, instance, created, **kwargs):
    if not created:
        return

    create_kwargs = {
        'weblogname': kwargs.get('weblogname', settings.PINGING_WEBLOG_NAME),
        'weblogurl': kwargs.get('weblogurl', settings.PINGING_WEBLOG_URL),
        }

    if hasattr(instance, 'get_absolute_url'):
        try:
            create_kwargs['changesurl'] = instance.get_absolute_url()
        except:
            # the changesurl is only a nice-to-have
            pass

    PingedURL.objects.create_for_servers(**create_kwargs)
