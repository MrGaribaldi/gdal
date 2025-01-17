#!/usr/bin/env pytest
# -*- coding: utf-8 -*-
###############################################################################
# $Id$
#
# Project:  GDAL/OGR Test Suite
# Purpose:  Test Geolocation warper.
# Author:   Frank Warmerdam <warmerdam@pobox.com>
#
###############################################################################
# Copyright (c) 2007, Frank Warmerdam <warmerdam@pobox.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################

import array
from osgeo import gdal, osr

import gdaltest
import pytest

###############################################################################
# Verify warped result.


def test_geoloc_1():

    tst = gdaltest.GDALTest('VRT', 'warpsst.vrt', 1, 61957)
    return tst.testOpen(check_filelist=False)


###############################################################################
# Test that we take into account the min/max of the geoloc arrays


def test_geoloc_bounds():

    lon_ds = gdal.GetDriverByName('GTiff').Create('/vsimem/lon.tif', 360, 1, 1, gdal.GDT_Float32)
    lon_ds.WriteRaster(0, 0, 360, 1, array.array('f', [91 + 0.5 * x for x in range(178)] + [-179.9 + 0.5 * x for x in range(182)]))
    lon_ds = None

    lat_ds = gdal.GetDriverByName('GTiff').Create('/vsimem/lat.tif', 80, 1, 1, gdal.GDT_Float32)
    lat_ds.WriteRaster(0, 0, 80, 1, array.array('f', [60.4 + 0.5 * x for x in range(60)] + [89 - 0.5 * x for x in range(20)]))
    lat_ds = None

    ds = gdal.GetDriverByName('MEM').Create('', 360, 80)
    md = {
        'LINE_OFFSET': '0',
        'LINE_STEP': '1',
        'PIXEL_OFFSET': '0',
        'PIXEL_STEP': '1',
        'X_DATASET': '/vsimem/lon.tif',
        'X_BAND' : '1',
        'Y_DATASET': '/vsimem/lat.tif',
        'Y_BAND' : '1',
        'SRS': 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST],AUTHORITY["EPSG","4326"]]'
    }
    ds.SetMetadata(md, 'GEOLOCATION')
    warped_ds = gdal.Warp('', ds, format='MEM')
    assert warped_ds

    gdal.Unlink('/vsimem/lon.tif')
    gdal.Unlink('/vsimem/lat.tif')

    gt = warped_ds.GetGeoTransform()
    assert gt[0] == pytest.approx(-179.9)
    assert gt[3] == pytest.approx(60.4 + 0.5 * 59)

###############################################################################
# Test that the line filling logic works


def test_geoloc_fill_line():


    ds = gdal.GetDriverByName('MEM').Create('', 200, 372)
    md = {
        'LINE_OFFSET': '0',
        'LINE_STEP': '1',
        'PIXEL_OFFSET': '0',
        'PIXEL_STEP': '1',
        'X_DATASET': '../alg/data/geoloc/longitude_including_pole.tif',
        'X_BAND' : '1',
        'Y_DATASET': '../alg/data/geoloc/latitude_including_pole.tif',
        'Y_BAND' : '1',
        'SRS': 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST],AUTHORITY["EPSG","4326"]]'
    }
    ds.SetMetadata(md, 'GEOLOCATION')
    ds.GetRasterBand(1).Fill(1)
    warped_ds = gdal.Warp('', ds, format='MEM')
    assert warped_ds
    assert warped_ds.GetRasterBand(1).Checksum() == 25798



###############################################################################
# Test warping from rectified to referenced-by-geoloc


def test_geoloc_warp_to_geoloc():

    lon_ds = gdal.GetDriverByName('GTiff').Create('/vsimem/lon.tif', 10, 1, 1, gdal.GDT_Float32)
    lon_ds.WriteRaster(0, 0, 10, 1, array.array('f', [-79.5 + 1 * x for x in range(10)]))
    lon_ds = None

    lat_ds = gdal.GetDriverByName('GTiff').Create('/vsimem/lat.tif', 10, 1, 1, gdal.GDT_Float32)
    lat_ds.WriteRaster(0, 0, 10, 1, array.array('f', [49.5 - 1 * x for x in range(10)]))
    lat_ds = None

    ds = gdal.GetDriverByName('MEM').Create('', 10, 10)
    md = {
        'LINE_OFFSET': '0',
        'LINE_STEP': '1',
        'PIXEL_OFFSET': '0',
        'PIXEL_STEP': '1',
        'X_DATASET': '/vsimem/lon.tif',
        'X_BAND' : '1',
        'Y_DATASET': '/vsimem/lat.tif',
        'Y_BAND' : '1',
        'SRS': 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST],AUTHORITY["EPSG","4326"]]'
    }
    ds.SetMetadata(md, 'GEOLOCATION')

    input_ds = gdal.GetDriverByName('MEM').Create('', 10, 10)
    input_ds.SetGeoTransform([-80, 1, 0, 50, 0, -1])
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    input_ds.SetSpatialRef(srs)
    input_ds.GetRasterBand(1).Fill(255)

    transformer = gdal.Transformer(input_ds, ds, [])

    success, pnt = transformer.TransformPoint(0, 0.5, 0.5)
    assert success
    assert pnt == pytest.approx((0.5, 0.5, 0))

    ds.GetRasterBand(1).Fill(0)
    assert gdal.Warp(ds, input_ds)

    assert ds.GetRasterBand(1).ComputeRasterMinMax() == (255, 255), ds.ReadAsArray()

    # Try with projected coordinates
    input_ds = gdal.GetDriverByName('MEM').Create('', 10, 10)
    input_ds.SetGeoTransform([-8905559.26346189, (-7792364.35552915 - -8905559.26346189)/10, 0, 6446275.84101716, 0, -(6446275.84101716-4865942.27950318)/10])
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3857)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    input_ds.SetSpatialRef(srs)
    input_ds.GetRasterBand(1).Fill(255)

    transformer = gdal.Transformer(input_ds, ds, [])

    success, pnt = transformer.TransformPoint(0, 0.5, 0.5)
    assert success
    assert pnt == pytest.approx((0.5, 0.5, 0), abs=0.1)

    ds.GetRasterBand(1).Fill(0)
    assert gdal.Warp(ds, input_ds)

    assert ds.GetRasterBand(1).ComputeRasterMinMax() == (255, 255), ds.ReadAsArray()


    gdal.Unlink('/vsimem/lon.tif')
    gdal.Unlink('/vsimem/lat.tif')



###############################################################################
# Test error cases


def test_geoloc_error_cases():

    lon_ds = gdal.GetDriverByName('GTiff').Create('/vsimem/lon.tif', 10, 1, 1, gdal.GDT_Float32)
    lon_ds.WriteRaster(0, 0, 10, 1, array.array('f', [-179.5 + 1 * x for x in range(10)]))
    lon_ds = None

    lat_ds = gdal.GetDriverByName('GTiff').Create('/vsimem/lat.tif', 10, 1, 1, gdal.GDT_Float32)
    lat_ds.WriteRaster(0, 0, 10, 1, array.array('f', [89.5 - 1 * x for x in range(10)]))
    lat_ds = None

    ds = gdal.GetDriverByName('MEM').Create('', 10, 10)
    ds.SetMetadata({'invalid': 'content'}, 'GEOLOCATION')

    with gdaltest.error_handler():
        transformer = gdal.Transformer(ds, None, [])
    assert transformer is None

    with gdaltest.error_handler():
        transformer = gdal.Transformer(None, ds, [])
    assert transformer is None

    gdal.Unlink('/vsimem/lon.tif')
    gdal.Unlink('/vsimem/lat.tif')
