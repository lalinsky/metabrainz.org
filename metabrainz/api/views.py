from flask import Blueprint, jsonify, send_from_directory, current_app, render_template
from flask.helpers import safe_join
from werkzeug.wrappers import Response
from werkzeug.urls import iri_to_uri
from metabrainz.api.decorators import token_required, tracked
import logging
import re
import os

api_bp = Blueprint('api', __name__)

NGINX_INTERNAL_LOCATION = '/internal/replication'

MIMETYPE_ARCHIVE = 'application/x-tar-bz2'
MIMETYPE_SIGNATURE = 'text/plain'

DAILY_SUBDIR = 'daily'
WEEKLY_SUBDIR = 'weekly'


@api_bp.route('/')
def info():
    """This view provides information about using the API."""
    return render_template('api/info.html')


@api_bp.route('/musicbrainz/replication-info')
@token_required
def replication_info():
    """This endpoint returns numbers of the last available replication packets."""

    def _get_last_packet_name(location, pattern):
        try:
            entries = [os.path.join(location, e) for e in os.listdir(location)]
        except OSError as e:
            logging.warning(e)
            return None
        pattern = re.compile(pattern)
        entries = filter(lambda x: pattern.search(x), entries)
        entries = filter(os.path.isfile, entries)
        entries.sort(reverse=True)  # latest first
        return os.path.split(entries[0])[-1] if entries else None

    # TODO(roman): Cache this response:
    return jsonify({
        'last_packet': _get_last_packet_name(
            current_app.config['REPLICATION_PACKETS_DIR'],
            "replication-[0-9]+.tar.bz2$"
        ),
        'last_packet_daily': _get_last_packet_name(
            os.path.join(current_app.config['REPLICATION_PACKETS_DIR'], DAILY_SUBDIR),
            "replication-daily-[0-9]+.tar.bz2$"
        ),
        'last_packet_weekly': _get_last_packet_name(
            os.path.join(current_app.config['REPLICATION_PACKETS_DIR'], WEEKLY_SUBDIR),
            "replication-weekly-[0-9]+.tar.bz2$"
        ),
    })


@api_bp.route('/musicbrainz/replication-<int:packet_number>.tar.bz2')
@token_required
@tracked
def replication_hourly(packet_number):
    directory = current_app.config['REPLICATION_PACKETS_DIR']
    filename = 'replication-%s.tar.bz2' % packet_number
    if not os.path.isfile(safe_join(directory, filename)):
        return Response("Can't find specified replication packet!\n", status=404)

    if 'USE_NGINX_X_ACCEL' in current_app.config and current_app.config['USE_NGINX_X_ACCEL']:
        return _redirect_to_nginx(os.path.join(NGINX_INTERNAL_LOCATION, filename))
    else:
        return send_from_directory(directory, filename, mimetype=MIMETYPE_ARCHIVE)


@api_bp.route('/musicbrainz/replication-<int:packet_number>.tar.bz2.asc')
@token_required
def replication_hourly_signature(packet_number):
    directory = current_app.config['REPLICATION_PACKETS_DIR']
    filename = 'replication-%s.tar.bz2.asc' % packet_number
    if not os.path.isfile(safe_join(directory, filename)):
        return Response("Can't find signature for a specified replication packet!\n", status=404)

    if 'USE_NGINX_X_ACCEL' in current_app.config and current_app.config['USE_NGINX_X_ACCEL']:
        return _redirect_to_nginx(os.path.join(NGINX_INTERNAL_LOCATION, filename))
    else:
        return send_from_directory(directory, filename, mimetype=MIMETYPE_SIGNATURE)


@api_bp.route('/musicbrainz/replication-daily-<int:packet_number>.tar.bz2')
@token_required
@tracked
def replication_daily(packet_number):
    directory = os.path.join(current_app.config['REPLICATION_PACKETS_DIR'], DAILY_SUBDIR)
    filename = 'replication-daily-%s.tar.bz2' % packet_number
    if not os.path.isfile(safe_join(directory, filename)):
        return Response("Can't find specified replication packet!\n", status=404)

    if 'USE_NGINX_X_ACCEL' in current_app.config and current_app.config['USE_NGINX_X_ACCEL']:
        return _redirect_to_nginx(os.path.join(NGINX_INTERNAL_LOCATION, DAILY_SUBDIR, filename))
    else:
        return send_from_directory(directory, filename, mimetype=MIMETYPE_ARCHIVE)


@api_bp.route('/musicbrainz/replication-daily-<int:packet_number>.tar.bz2.asc')
@token_required
def replication_daily_signature(packet_number):
    directory = os.path.join(current_app.config['REPLICATION_PACKETS_DIR'], DAILY_SUBDIR)
    filename = 'replication-daily-%s.tar.bz2.asc' % packet_number
    if not os.path.isfile(safe_join(directory, filename)):
        return Response("Can't find signature for a specified replication packet!\n", status=404)

    if 'USE_NGINX_X_ACCEL' in current_app.config and current_app.config['USE_NGINX_X_ACCEL']:
        return _redirect_to_nginx(os.path.join(NGINX_INTERNAL_LOCATION, DAILY_SUBDIR, filename))
    else:
        return send_from_directory(directory, filename, mimetype=MIMETYPE_SIGNATURE)


@api_bp.route('/musicbrainz/replication-weekly-<int:packet_number>.tar.bz2')
@token_required
@tracked
def replication_weekly(packet_number):
    directory = os.path.join(current_app.config['REPLICATION_PACKETS_DIR'], WEEKLY_SUBDIR)
    filename = 'replication-weekly-%s.tar.bz2' % packet_number
    if not os.path.isfile(safe_join(directory, filename)):
        return Response("Can't find specified replication packet!\n", status=404)

    if 'USE_NGINX_X_ACCEL' in current_app.config and current_app.config['USE_NGINX_X_ACCEL']:
        return _redirect_to_nginx(os.path.join(NGINX_INTERNAL_LOCATION, WEEKLY_SUBDIR, filename))
    else:
        return send_from_directory(directory, filename, mimetype=MIMETYPE_ARCHIVE)


@api_bp.route('/musicbrainz/replication-weekly-<int:packet_number>.tar.bz2.asc')
@token_required
def replication_weekly_signature(packet_number):
    directory = os.path.join(current_app.config['REPLICATION_PACKETS_DIR'], WEEKLY_SUBDIR)
    filename = 'replication-weekly-%s.tar.bz2.asc' % packet_number
    if not os.path.isfile(safe_join(directory, filename)):
        return Response("Can't find signature for a specified replication packet!\n", status=404)

    if 'USE_NGINX_X_ACCEL' in current_app.config and current_app.config['USE_NGINX_X_ACCEL']:
        return _redirect_to_nginx(os.path.join(NGINX_INTERNAL_LOCATION, WEEKLY_SUBDIR, filename))
    else:
        return send_from_directory(directory, filename, mimetype=MIMETYPE_SIGNATURE)


def _redirect_to_nginx(location):
    """This creates an internal redirection to a specified location.

    This feature is only supported by nginx. See http://wiki.nginx.org/X-accel
    for more information about it.
    """
    response = Response(status=200)
    location = iri_to_uri(location, safe_conversion=True)
    response.headers['X-Accel-Redirect'] = location
    return response
