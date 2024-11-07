from functools import partial, wraps
from typing import Any, Callable

import geopandas
import numpy as np
import pyproj
from folium import GeoJson
from geodatasets import get_path
from geopandas import GeoDataFrame, GeoSeries, read_file
from geopandas.tools import geocode as geopanda_geocode
from geopandas.tools import reverse_geocode
from shapely import Point, transform
from shapely.geometry.base import BaseGeometry

from ..cell_range import CellRange, unproxy_for_dataframe
from ..spreadsheet_error import UNSUPPORTED_ERROR, VALUE_ERROR


def transform_coord_to_meters(center_lat, center_lng, args):
    source_proj = pyproj.Proj(init="epsg:4326")
    target_proj = pyproj.Proj(proj="aeqd", lat_0=center_lat, lon_0=center_lng)
    res = pyproj.transform(source_proj, target_proj, args[:, 0], args[:, 1])
    return np.array(res).T


def with_geodata_frames(func: Callable):
    def maybe_to_dataframe(arg: Any) -> Any:
        if isinstance(arg, CellRange) and arg.two_dimensional:
            return arg.to_geodataframe()
        return arg

    @wraps(func)
    def wrapper(*args, **kwargs):
        args = [maybe_to_dataframe(arg) for arg in args]
        kwargs = {key: maybe_to_dataframe(value) for key, value in kwargs.items()}
        return func(*args, **kwargs)

    return wrapper


@with_geodata_frames
def plot(gdf: GeoDataFrame, *args, **kwargs):
    gdf.plot(*args, **kwargs)


@with_geodata_frames
def explore(target: CellRange, *args, **kwargs):
    """Show a map of the given target(s)."""
    if "tiles" not in kwargs:
        kwargs["tiles"] = "cartodbpositron"

    not_mappable = [arg for arg in args if not isinstance(arg, GeoDataFrame)]

    res = None
    for arg in [target, *args]:
        if isinstance(arg, GeoDataFrame):
            if res is None:
                # Support multiple geo columns:
                def is_geo_column(col):
                    return all(isinstance(x, BaseGeometry) for x in arg[col])

                filtered = GeoDataFrame(
                    arg[
                        [
                            col
                            for col in arg.columns
                            if not is_geo_column(col) or col == arg.geometry.name
                        ]
                    ],
                ).copy()

                res = filtered.explore(*not_mappable, **kwargs)
                for col in arg.columns:
                    if is_geo_column(col) and col != arg.geometry.name:
                        geojson_data = GeoSeries(arg[col].dropna()).to_json()
                        res.add_child(GeoJson(geojson_data, name=col))
            else:
                res.add_child(GeoJson(arg))
    if res is None:
        return VALUE_ERROR.with_message("No mappable objects found")
    return res


def dataset(name_or_url: str) -> GeoDataFrame:
    """Returns a sample dataset given a name or url.

    Named datasets are taken from geopandas.datasets, geoplot.datasets and geodatasets.
    geoplot is not by default installed, so you need to set it up if you want to depend
    on that.

    Example:
        =geo.dataset("naturalearth_lowres")
        -- returns a GeoDataFrame with countries
    """
    if "://" in name_or_url:
        path = name_or_url
    else:
        if name_or_url in geopandas.datasets.available:
            path = geopandas.datasets.get_path(name_or_url)
        else:
            import geoplot
            try:
                path = geoplot.datasets.get_path(name_or_url)
            except ValueError:
                path = get_path(name_or_url)
    gdf = read_file(path)
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    else:
        gdf = gdf.to_crs(epsg=4326)
    return gdf


def geo_call(convert_to_meters=True):
    def decorator(func: Callable):
        def convert_arg(arg: Any) -> Any:
            if isinstance(arg, BaseGeometry):
                return unproxy_for_dataframe(arg)
            if isinstance(arg, CellRange):
                arg = arg.to_geodataframe()
            if isinstance(arg, GeoDataFrame):
                arg = arg.geometry
            if isinstance(arg, GeoSeries):
                arg = [unproxy_for_dataframe(shape) for shape in arg]
            return arg

        def get_centroid(args):
            lat_sum = 0
            lng_sum = 0
            count = 0
            for arg in args:
                if isinstance(arg, BaseGeometry):
                    lat_sum += arg.centroid.y
                    lng_sum += arg.centroid.x
                    count += 1
                elif isinstance(arg, list):
                    for shape in arg:
                        if isinstance(shape, BaseGeometry):
                            lat_sum += shape.centroid.y
                            lng_sum += shape.centroid.x
                            count += 1
            if count == 0:
                return None, None
            return lat_sum / count, lng_sum / count

        def maybe_transform(arg, to_meters):
            if isinstance(arg, BaseGeometry):
                return transform(arg, to_meters)
            if isinstance(arg, list):
                return [maybe_transform(shape, to_meters) for shape in arg]
            return arg

        @wraps(func)
        def wrapper(*args, **kwargs):
            args = [convert_arg(arg) for arg in args]
            if convert_to_meters:
                center_lat, center_lng = get_centroid(args)
                to_meters = partial(transform_coord_to_meters, center_lat, center_lng)
                args = [maybe_transform(arg, to_meters) for arg in args]
                kwargs = {key: convert_arg(value) for key, value in kwargs.items()}
            method = getattr(args[0], func.__name__, None)
            if isinstance(method, float) or isinstance(method, int):
                # If the method is a number, it means that we are dealing with a property:
                return method
            if method is None:
                return UNSUPPORTED_ERROR.with_message(
                    f"Can't call {func.__name__} with these arguments"
                )

            return method(*args[1:], **kwargs)

        return wrapper

    return decorator


@geo_call(convert_to_meters=True)
def area(target: CellRange | BaseGeometry) -> float | list[float]:
    """Returns the area in square meters of the given target.

    target: shape or cell range containing shapes
    """


@geo_call(convert_to_meters=True)
def distance(target: BaseGeometry, other: BaseGeometry) -> float:
    """Returns the distance in meters between two shapes or cell ranges.

    Example:
        =geo.distance(A1, geo.geocode("Amsterdam"))
        - returns the distance between A1 and Amsterdam in meters
    """


@geo_call(convert_to_meters=True)
def hausdorff_distance(target: BaseGeometry, other: BaseGeometry) -> float:
    """The Hausdorff distance is the maximum distance from a point in target to the nearest point in other

    It's a way to quantify the dissimilarity between two geometric shapes.
    This measurement can be especially useful in spatial analysis and
    computational geometry tasks.
    """


@geo_call(convert_to_meters=True)
def length(target: BaseGeometry) -> float:
    """Returns the length in meters of the given target"""


@geo_call(convert_to_meters=False)
def boundary(target: BaseGeometry) -> BaseGeometry:
    """Returns a lower dimension geometry that bounds the object

    The boundary of a polygon is a line, the boundary of a line is a
    collection of points. The boundary of a point is an empty (null)
    collection."""


@geo_call(convert_to_meters=False)
def centroid(target: BaseGeometry) -> Point:
    """Returns the geometric center of the object

    The centroid is equal to the centroid of the set of component
    Geometries of highest dimension (since the lower-dimension
    geometries contribute zero "weight" to the centroid)."""


def geocode(query: str | list[str]) -> Point | GeoDataFrame:
    """Returns the coordinates of the given query.

    Example:
        =geo.geocode("Amsterdam")
        -- returns a Point with the coordinates of Amsterdam
    """
    res = geopanda_geocode(query)
    if isinstance(query, str):
        return res.geometry.iloc[0]
    else:
        return res


@geo_call(convert_to_meters=False)
def difference(element1: BaseGeometry, element2: BaseGeometry) -> BaseGeometry:
    """Returns the part of element1 that is not covered by element2."""


@geo_call(convert_to_meters=False)
def intersection(element1: BaseGeometry, element2: BaseGeometry) -> BaseGeometry:
    """Returns the part of element1 that is covered by element2."""


@geo_call(convert_to_meters=False)
def symmetric_difference(
    element1: BaseGeometry, element2: BaseGeometry
) -> BaseGeometry:
    """Returns the parts of element1 and element2 that are not covered by the other"""


@geo_call(convert_to_meters=False)
def union(element1: BaseGeometry, element2: BaseGeometry) -> BaseGeometry:
    """Returns the union of element1 and element2"""


@with_geodata_frames
def sjoin(
    element1: GeoDataFrame,
    element2: GeoDataFrame,
    *,
    how="inner",
    predicate="intersects",
    lsuffix="left",
    rsuffix="right",
) -> GeoDataFrame:
    """Spatial join of two GeoDataFrames.

    Returns a GeoDataFrame with a new column containing the index of the
    element in element2 that intersects with the element in element1.

    how : string, default 'inner'
         The type of join:

         * 'left': use keys from left_df; retain only left_df geometry column
         * 'right': use keys from right_df; retain only right_df geometry column
         * 'inner': use intersection of keys from both dfs; retain only
           left_df geometry column

     predicate : string, default 'intersects'
         Binary predicate. Valid values are determined by the spatial index used.
         You can check the valid values in left_df or right_df as
         ``left_df.sindex.valid_query_predicates`` or
         ``right_df.sindex.valid_query_predicates``
     lsuffix : string, default 'left'
         Suffix to apply to overlapping column names (left GeoDataFrame).
     rsuffix : string, default 'right'
         Suffix to apply to overlapping column names (right GeoDataFrame).
    """
    return element1.sjoin(
        element2, how=how, predicate=predicate, lsuffix=lsuffix, rsuffix=rsuffix
    )


@with_geodata_frames
def buffer(
    target: BaseGeometry,
    distance: float,
    quad_segs=16,
    cap_style="round",
    join_style="round",
    mitre_limit=5.0,
    single_sided=False,
) -> BaseGeometry:
    """Returns a geometry that represents all points whose distance from this
    geometry is less than or equal to distance.

    cap_style : shapely.BufferCapStyle or {'round', 'square', 'flat'}
    join_style : shapely.BufferJoinStyle or {'round', 'mitre', 'bevel'}
    """
    return target.buffer(
        distance,
        quad_segs=quad_segs,
        cap_style=cap_style,
        join_style=join_style,
        mitre_limit=mitre_limit,
        single_sided=single_sided,
    )


@with_geodata_frames
def convex_hull(target: BaseGeometry) -> BaseGeometry:
    """Returns the smallest convex Polygon that contains all the points in the
    geometry."""
    return target.convex_hull


@with_geodata_frames
def minimum_rotated_rectangle(target: BaseGeometry) -> BaseGeometry:
    """Returns the minimum rotated rectangle that contains all the points in the
    geometry."""
    return target.minimum_rotated_rectangle


@with_geodata_frames
def wkt(target: BaseGeometry) -> str:
    """Returns the Well Known Text representation of the given target."""
    return target.wkt()


@with_geodata_frames
def lat(target: BaseGeometry) -> float:
    """Returns the latitude of the given target."""
    return target.centroid.y


@with_geodata_frames
def lng(target: BaseGeometry) -> float:
    """Returns the longitude of the given target."""
    return target.centroid.x


__all__ = [
    "area",
    "boundary",
    "buffer",
    "centroid",
    "dataset",
    "difference",
    "distance",
    "explore",
    "geocode",
    "hausdorff_distance",
    "intersection",
    "lat",
    "lng",
    "length",
    "plot",
    "reverse_geocode",
    "sjoin",
    "symmetric_difference",
    "union",
    "wkt",
]
