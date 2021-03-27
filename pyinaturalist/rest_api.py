"""
Code used to access the (read/write, but slow) Rails based API of iNaturalist
See: https://www.inaturalist.org/pages/api+reference

Functions
---------

.. automodsumm:: pyinaturalist.rest_api
    :functions-only:
    :nosignatures:

"""
from typing import Any, List, Union
from warnings import warn

from pyinaturalist import api_docs as docs
from pyinaturalist.api_requests import delete, get, post, put
from pyinaturalist.auth import get_access_token  # noqa
from pyinaturalist.constants import API_V0_BASE_URL, FileOrPath, JsonResponse, ListResponse
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.forge_utils import document_request_params
from pyinaturalist.pagination import add_paginate_all, paginate_all
from pyinaturalist.request_params import (
    OBSERVATION_FORMATS,
    REST_OBS_ORDER_BY_PROPERTIES,
    convert_observation_fields,
    ensure_file_obj,
    ensure_file_objs,
    validate_multiple_choice_param,
)
from pyinaturalist.response_format import convert_all_coordinates, convert_all_timestamps


@document_request_params(
    [
        docs._observation_common,
        docs._observation_rest_only,
        docs._bounding_box,
        docs._pagination,
    ]
)
@add_paginate_all(method='page')
def get_observations(**params) -> Union[List, str]:
    """Get observation data, optionally in an alternative format. Also see
    :py:func:`.get_geojson_observations` for GeoJSON format (not included here because it wraps
    a separate API endpoint).

    **API reference:** https://www.inaturalist.org/pages/api+reference#get-observations

    Example:

        >>> get_observations(id=45414404, format='atom')

        .. admonition:: Example Response (atom)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.atom
                :language: xml

        .. admonition:: Example Response (csv)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.csv

        .. admonition:: Example Response (dwc)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.dwc
                :language: xml

        .. admonition:: Example Response (json)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.json
                :language: json

        .. admonition:: Example Response (kml)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.kml
                :language: xml

        .. admonition:: Example Response (widget)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.js
                :language: javascript

    Returns:
        Return type will be ``dict`` for the ``json`` response format, and ``str`` for all others.
    """
    response_format = params.pop('response_format', 'json')
    if response_format == 'geojson':
        raise ValueError('For geojson format, use pyinaturalist.node_api.get_geojson_observations')
    if response_format not in OBSERVATION_FORMATS:
        raise ValueError('Invalid response format')
    validate_multiple_choice_param(params, 'order_by', REST_OBS_ORDER_BY_PROPERTIES)

    response = get(
        f'{API_V0_BASE_URL}/observations.{response_format}',
        params=params,
    )

    if response_format == 'json':
        observations = response.json()
        observations = convert_all_coordinates(observations)
        observations = convert_all_timestamps(observations)
        return observations
    else:
        return response.text


@document_request_params([docs._search_query, docs._pagination])
@add_paginate_all(method='page')
def get_observation_fields(**params) -> JsonResponse:
    """Search observation fields. Observation fields are basically typed data fields that
    users can attach to observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#get-observation_fields

    Example:

        >>> get_observation_fields(q='number of individuals')
        >>> # Show just observation field IDs and names
        >>> from pprint import pprint
        >>> pprint({r['id']: r['name'] for r in response})

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_fields.py

    Returns:
        Observation fields as a list of dicts
    """
    response = get(
        f'{API_V0_BASE_URL}/observation_fields.json',
        params=params,
    )
    response.raise_for_status()

    obs_fields = response.json()
    obs_fields = convert_all_timestamps(obs_fields)
    return {'results': obs_fields}


@document_request_params([docs._search_query])
def get_all_observation_fields(**params) -> ListResponse:
    """[Deprecated] Like :py:func:`.get_observation_fields()`, but gets all pages of results"""
    warn(DeprecationWarning("Use get_observation_fields(page='all') instead"))
    return paginate_all(get_observation_fields, method='page', **params)['results']


def put_observation_field_values(
    observation_id: int,
    observation_field_id: int,
    value: Any,
    access_token: str,
    user_agent: str = None,
) -> JsonResponse:
    # TODO: Also implement a put_or_update_observation_field_values() that deletes then recreates the field_value?
    # TODO: Return some meaningful exception if it fails because the field is already set.
    # TODO: It appears pushing the same value/pair twice in a row (but deleting it meanwhile via the UI)...
    # TODO: ...triggers an error 404 the second time (report to iNaturalist?)
    """Set an observation field (value) on an observation.
    Will fail if this observation field is already set for this observation.

    To find an `observation_field_id`, either user :py:func:`.get_observation_fields` or search
    on iNaturalist: https://www.inaturalist.org/observation_fields

    **API reference:** https://www.inaturalist.org/pages/api+reference#put-observation_field_values-id

    Example:
            >>> # First find an observation field by name, if the ID is unknown
            >>> response = get_observation_fields('vespawatch_id')
            >>> observation_field_id = response[0]['id']
            >>>
            >>> put_observation_field_values(
            >>>     observation_id=7345179,
            >>>     observation_field_id=observation_field_id,
            >>>     value=250,
            >>>     access_token=token,
            >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/put_observation_field_value_result.json
                :language: javascript

    Args:
        observation_id: ID of the observation receiving this observation field value
        observation_field_id: ID of the observation field for this observation field value
        value: Value for the observation field
        access_token: access_token: The access token, as returned by :func:`get_access_token()`
        user_agent: A user-agent string that will be passed to iNaturalist.

    Returns:
        The newly updated field value record
    """

    payload = {
        'observation_field_value': {
            'observation_id': observation_id,
            'observation_field_id': observation_field_id,
            'value': value,
        }
    }

    response = put(
        f'{API_V0_BASE_URL}/observation_field_values/{observation_field_id}',
        access_token=access_token,
        user_agent=user_agent,
        json=payload,
    )

    response.raise_for_status()
    return response.json()


@document_request_params([docs._access_token, docs._create_observation])
def create_observation(access_token: str = None, **params) -> ListResponse:
    """Create a new observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#post-observations

    Example:
        >>> token = get_access_token()
        >>> create_observation(
        >>>     access_token=token,
        >>>     species_guess='Pieris rapae',
        >>>     local_photos='~/observation_photos/2020_09_01_14003156.jpg',
        >>>     observation_fields={297: 1},  # 297 is the obs. field ID for 'Number of individuals'
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/create_observation_result.json
                :language: javascript

        .. admonition:: Example Response (failure)
            :class: toggle

            .. literalinclude:: ../sample_data/create_observation_fail.json
                :language: javascript

    Returns:
        JSON response containing the newly created observation(s)

    Raises:
        :py:exc:`requests.HTTPError`, if the call is not successful. iNaturalist returns an
        error 422 (unprocessable entity) if it rejects the observation data (for example an
        observation date in the future or a latitude > 90. In that case the exception's
        ``response`` attribute gives more details about the errors.
    """
    # Accept either top-level params (like most other endpoints)
    # or nested {'observation': params} (like the iNat API accepts directly)
    if 'observation' in params:
        params.update(params.pop('observation'))
    params = convert_observation_fields(params)
    if 'local_photos' in params:
        params['local_photos'] = ensure_file_objs(params['local_photos'])

    response = post(
        url=f'{API_V0_BASE_URL}/observations.json',
        json={'observation': params},
        access_token=access_token,
    )
    response.raise_for_status()
    return response.json()


@document_request_params(
    [
        docs._observation_id,
        docs._access_token,
        docs._create_observation,
        docs._update_observation,
    ]
)
def update_observation(
    observation_id: int,
    access_token: str = None,
    **params,
) -> ListResponse:
    """
    Update a single observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#put-observations-id

    .. note::

        Unlike the underlying REST API endpoint, this function will **not** delete any existing
        photos from your observation if not specified in ``local_photos``. If you want this to
        behave the same as the REST API and you do want to delete photos, call with
        ``ignore_photos=False``.

    Example:

        >>> token = get_access_token()
        >>> update_observation(
        >>>     17932425,
        >>>     access_token=token,
        >>>     description='updated description!',
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/update_observation_result.json
                :language: javascript

    Returns:
        JSON response containing the newly updated observation(s)

    Raises:
        :py:exc:`requests.HTTPError`, if the call is not successful. iNaturalist returns an
            error 410 if the observation doesn't exists or belongs to another user.
    """
    # Accept either top-level params (like most other endpoints)
    # or nested params (like the iNat API actually accepts)
    if 'observation' in params:
        params.update(params.pop('observation'))
    params = convert_observation_fields(params)
    if 'local_photos' in params:
        params['local_photos'] = ensure_file_objs(params['local_photos'])

    # This is the one Boolean parameter that's specified as an int, for some reason.
    # Also, set it to True if not specified, which seems like much saner default behavior.
    if 'ignore_photos' in params:
        params['ignore_photos'] = int(params['ignore_photos'])
    else:
        params['ignore_photos'] = 1

    response = put(
        url=f'{API_V0_BASE_URL}/observations/{observation_id}.json',
        json={'observation': params},
        access_token=access_token,
    )
    response.raise_for_status()
    return response.json()


def add_photo_to_observation(
    observation_id: int,
    photo: FileOrPath,
    access_token: str,
    user_agent: str = None,
):
    """Upload a local photo and assign it to an existing observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#post-observation_photos

    Example:

        >>> token = get_access_token()
        >>> add_photo_to_observation(
        >>>     1234,
        >>>     '~/observation_photos/2020_09_01_14003156.jpg',
        >>>     access_token=token,
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/add_photo_to_observation.json
                :language: javascript

    Args:
        observation_id: the ID of the observation
        photo: An image file, file-like object, or path
        access_token: the access token, as returned by :func:`get_access_token()`
        user_agent: a user-agent string that will be passed to iNaturalist.

    Returns:
        Information about the newly created photo
    """
    response = post(
        url=f'{API_V0_BASE_URL}/observation_photos',
        access_token=access_token,
        data={'observation_photo[observation_id]': observation_id},
        files={'file': ensure_file_obj(photo)},
        user_agent=user_agent,
    )

    return response.json()


@document_request_params([docs._observation_id, docs._access_token])
def delete_observation(observation_id: int, access_token: str = None, user_agent: str = None):
    """
    Delete an observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#delete-observations-id

    Example:

        >>> token = get_access_token()
        >>> delete_observation(17932425, token)

    Returns:
        If successful, no response is returned from this endpoint

    Raises:
        :py:exc:`.ObservationNotFound` if the requested observation doesn't exist
        :py:exc:`requests.HTTPError` (403) if the observation belongs to another user
    """
    response = delete(
        url=f'{API_V0_BASE_URL}/observations/{observation_id}.json',
        access_token=access_token,
        headers={'Content-type': 'application/json'},
        user_agent=user_agent,
    )
    if response.status_code == 404:
        raise ObservationNotFound
    response.raise_for_status()
