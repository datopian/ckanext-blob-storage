"""ckanext-blob-storage Flask blueprints
"""
from ckan.plugins import toolkit
from flask import Blueprint, request

from .download_handler import call_download_handlers, call_pre_download_handlers, get_context

blueprint = Blueprint(
    'blob_storage',
    __name__,
)


def download(id, resource_id, filename=None):
    """Download resource blueprint

    This calls all registered download handlers in order, until
    a response is returned to the user
    """
    context = get_context()
    activity_id = toolkit.request.params.get('activity_id')
    resource = None
    try:
        resource = toolkit.get_action('resource_show')(context, {'id': resource_id})
        if id != resource['package_id']:
            return toolkit.abort(404, toolkit._('Resource not found belonging to package'))

        inline = toolkit.asbool(request.args.get('preview'))

        package = toolkit.get_action('package_show')(context, {'id': id})
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._('Dataset not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Not authorized to read package {0}'.format(id)))

    if activity_id:
        try:
            activity = toolkit.get_action(u'activity_show')(
                context, {u'id': activity_id, u'include_data': True})
            activity_dataset = activity['data']['package']
            assert activity_dataset['id'] == id
            activity_resources = activity_dataset['resources']
            for r in activity_resources:
                if r['id'] == resource_id:
                    resource = r
                    package = activity_dataset
                    break
        except toolkit.NotFound:
            toolkit.abort(404, toolkit._(u'Activity not found'))

    if not resource:
        try:
            resource = toolkit.get_action('resource_show')(context, {'id': resource_id})
            if id != resource['package_id']:
                return toolkit.abort(404, toolkit._('Resource not found belonging to package'))
        except toolkit.ObjectNotFound:
            return toolkit.abort(404, toolkit._('Resource not found'))

    try:
        resource = call_pre_download_handlers(resource, package, activity_id=activity_id)
        return call_download_handlers(resource, package, filename, inline, activity_id=activity_id)
    except toolkit.ObjectNotFound:
            return toolkit.abort(404, toolkit._('Resource not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Not authorized to read resource {0}'.format(resource_id)))


blueprint.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download', view_func=download)
blueprint.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download/<filename>', view_func=download)
