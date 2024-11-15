"""AMDA_Webservice utility functions. This module defines some conversion functions specific to AMDA_Webservice, mainly
conversion procedures for parsing CSV and VOTable data.

"""
import datetime
import logging
import os
import re
import tempfile
from typing import Dict, List

import numpy as np
import pandas as pds
from speasy.config import amda as amda_cfg
from speasy.core import epoch_to_datetime64
from speasy.core.any_files import any_loc_open
from speasy.core.datetime_range import DateTimeRange
from speasy.products.catalog import Catalog, Event
from speasy.products.timetable import TimeTable
from speasy.products.variable import (DataContainer, SpeasyVariable,
                                      VariableAxis, VariableTimeAxis)

log = logging.getLogger(__name__)

DATA_CHUNK_SIZE = 10485760

def _build_event(data, colnames: List[str]) -> Event:
    return Event(datetime.datetime.strptime(data[0], "%Y-%m-%dT%H:%M:%S.%f"),
                 datetime.datetime.strptime(data[1], "%Y-%m-%dT%H:%M:%S.%f"),
                 {name: value for name, value in zip(colnames[2:], data[2:])})


def load_timetable(filename: str) -> TimeTable:
    """Load a timetable file

    Parameters
    ----------
    filename: str
        filename

    Returns
    -------
    TimeTable
        File content loaded as TimeTable
    """
    if '://' not in filename:
        filename = f"file://{os.path.abspath(filename)}"
    with any_loc_open(filename) as votable:
        # save the timetable as a dataframe, speasy.common.SpeasyVariable
        # get header data first

        from astropy.io.votable import parse as parse_votable
        votable = parse_votable(votable)
        name = next(filter(lambda e: 'Name' in e,
                           votable.description.split(';\n'))).split(':')[-1]
        # convert astropy votable structure to SpeasyVariable
        tab = votable.get_first_table()
        # prepare data
        data = tab.array.tolist()
        dt_ranges = [DateTimeRange(datetime.datetime.strptime(t0, "%Y-%m-%dT%H:%M:%S.%f"),
                                   datetime.datetime.strptime(t1, "%Y-%m-%dT%H:%M:%S.%f")) for (t0, t1) in
                     data]
        var = TimeTable(name=name, meta={}, dt_ranges=dt_ranges)
        return var


def load_catalog(filename: str) -> Catalog:
    """Load a timetable file

    Parameters
    ----------
    filename: str
        filename

    Returns
    -------
    Catalog
        File content loaded as Catalog

    """
    if '://' not in filename:
        filename = f"file://{os.path.abspath(filename)}"
    with any_loc_open(filename) as votable:
        # save the timetable as a dataframe, speasy.common.SpeasyVariable
        # get header data first

        from astropy.io.votable import parse as parse_votable
        votable = parse_votable(votable)
        # convert astropy votable structure to SpeasyVariable
        tab = votable.get_first_table()
        name = next(filter(lambda e: 'Name' in e,
                           votable.description.split(';\n'))).split(':')[-1]
        colnames = list(map(lambda f: f.name, tab.fields))
        data = tab.array.tolist()
        events = [_build_event(line, colnames) for line in data]
        var = Catalog(name=name, meta={}, events=events)
        return var


def get_parameter_args(start_time: datetime, stop_time: datetime, product: str, **kwargs) -> Dict:
    """Get parameter arguments

    Parameters
    ----------
    start_time: datetime
        parameter start time
    stop_time: datetime
        parameter stop time
    product: str
        product ID (xmlid)

    Returns
    -------
    dict
        parameter arguments in dictionary
    """
    return {'path': f"amda/{product}", 'start_time': f'{start_time.isoformat()}',
            'stop_time': f'{stop_time.isoformat()}',
            'output_format': kwargs.get('output_format', amda_cfg.output_format.get())}
