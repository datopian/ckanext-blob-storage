"""ckanext-external-storage Flask blueprints
"""
import logging

from ckan.common import request
from ckan.plugins import toolkit
from flask import Blueprint

from .download_handler import call_download_handlers, call_pre_download_handlers, get_context

log = logging.getLogger(__name__)

blueprint = Blueprint(
    'extstorage',
    __name__,
)


def download(dataset_id, resource_id, filename=None):
    """Download resource blueprint

    This calls all registered download handlers in order, until
    a response is returned to the user
    """
    activity_id = request.args.get('activity_id')
    log.error("UNAIDS resource download")
    context = get_context()
    resource = None
    try:
        package = toolkit.get_action('package_show')(context, {'id': dataset_id})
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._('Dataset not found'))
    if activity_id:
        try:
            activity = toolkit.get_action(u'activity_show')(
                context, {u'id': activity_id, u'include_data': True})
            activity_dataset = activity['data']['package']
            assert activity_dataset['id'] == dataset_id
            activity_resources = activity_dataset['resources']
            for r in activity_resources:
                if r['id'] == resource_id:
                    resource = r
                    package = activity_dataset
                    break

        except toolkit.NotFound:
            toolkit.abort(404, toolkit._(u'Activity not found'))
    try:
        if not resource:
            resource = toolkit.get_action('resource_show')(context, {'id': resource_id})
            if dataset_id != resource['package_id']:
                return toolkit.abort(404, toolkit._('Resource not found belonging to package'))

        resource = call_pre_download_handlers(resource, package, activity_id=activity_id)
        return call_download_handlers(resource, package, filename, activity_id=activity_id)

    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._('Resource not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, toolkit._('Not authorized to read resource {0}'.format(resource_id)))


blueprint.add_url_rule(u'/dataset/<dataset_id>/resource/<resource_id>/download', view_func=download)
blueprint.add_url_rule(u'/dataset/<dataset_id>/resource/<resource_id>/download/<filename>', view_func=download)
