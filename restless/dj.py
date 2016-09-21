from distutils.version import StrictVersion
import six

from django import get_version as get_django_version
from django.conf import settings
if StrictVersion(get_django_version()) >= StrictVersion('1.7.0'):
    from django.conf.urls import url
else:
    from django.conf.urls import patterns, url

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from .exceptions import NotFound
from .resources import Resource


class DjangoResource(Resource):
    """
    A Django-specific ``Resource`` subclass.

    Doesn't require any special configuration, but helps when working in a
    Django environment.
    """
    # Because Django.
    @classmethod
    def as_list(cls, *args, **kwargs):
        return csrf_exempt(super(DjangoResource, cls).as_list(*args, **kwargs))

    @classmethod
    def as_detail(cls, *args, **kwargs):
        return csrf_exempt(super(DjangoResource, cls).as_detail(*args, **kwargs))

    def is_debug(self):
        # By default, Django-esque.
        return settings.DEBUG

    def build_response(self, data, status=200):
        # By default, Django-esque.
        resp = HttpResponse(data, content_type='application/json')
        resp.status_code = status
        return resp

    def build_error(self, err):
        # A bit nicer behavior surrounding things that don't exist.
        if isinstance(err, (ObjectDoesNotExist, Http404)):
            err = NotFound(msg=six.text_type(err))

        return super(DjangoResource, self).build_error(err)

    @classmethod
    def build_url_name(cls, name, name_prefix=None):
        """
        Given a ``name`` & an optional ``name_prefix``, this generates a name
        for a URL.

        :param name: The name for the URL (ex. 'detail')
        :type name: string

        :param name_prefix: (Optional) A prefix for the URL's name (for
            resolving). The default is ``None``, which will autocreate a prefix
            based on the class name. Ex: ``BlogPostResource`` ->
            ``api_blog_post_list``
        :type name_prefix: string

        :returns: The final name
        :rtype: string
        """
        if name_prefix is None:
            name_prefix = 'api_{0}'.format(
                cls.__name__.replace('Resource', '').lower()
            )

        name_prefix = name_prefix.rstrip('_')
        return '_'.join([name_prefix, name])

    @classmethod
    def urls(cls, name_prefix=None):
        """
        A convenience method for hooking up the URLs.

        This automatically adds a list & a detail endpoint to your URLconf.

        :param name_prefix: (Optional) A prefix for the URL's name (for
            resolving). The default is ``None``, which will autocreate a prefix
            based on the class name. Ex: ``BlogPostResource`` ->
            ``api_blogpost_list``
        :type name_prefix: string

        :returns: A ``patterns`` or a ``list`` object for ``include(...)``
        """
        urls = [
            url(r'^$', cls.as_list(), name=cls.build_url_name('list', name_prefix)),
            url(r'^(?P<pk>\d+)/$', cls.as_detail(), name=cls.build_url_name('detail', name_prefix)),
        ]
        if StrictVersion(get_django_version()) >= StrictVersion('1.7.0'):
            return urls
        return patterns('', urls[0], urls[1])
