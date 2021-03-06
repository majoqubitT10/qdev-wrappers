from collections import defaultdict
from qdev_wrappers.show_num import show_num
from functools import reduce
import operator
from dateutil import parser

from . import get_metadata_list


def load(counter, plot=True, metadata=True, matplot=False):
    """
    Function like shownum which loads dataset, (optionally) plots it in
    QtPlot  (or matplot) from default location and (optionally) prints
    metadata for that measurement given metadata_list values

    Args:
        counter (int)
        plot(default True): do you want to return plots as well as dataset?
        metadata (default True): do you want to print the metadata?
        matplot (bool) (default False): default is to QtPlot the data

    Returns:
        dataset (qcodes DataSet)
        plot (QtPlot or Matplot): optional
    """
    useQT = not matplot
    dataset, plots = show_num(counter, do_plot=plot, useQT=useQT)
    if metadata:
        _ = get_metadata(dataset, printout=True)
        _ = _get_data_duration(dataset)
    return dataset, plots


def get_metadata(dataset, printout=True, specific_list=None):
    """
    Function which gets the metadata dictionary for a dataset.

    Args:
        dataset(qcodes dataset or int): dataset for which we want metadata
        printout (default True): should metadata be printed as well as
            returned?
        specific_list (default None):

    Returns:
        meta_dict dictionary of the form:
            {'instr': {'param':
                            {'value': val,
                            'unit': u}}}
            for a parameter with name 'param' belonging to instrument 'instr'
            with value 'val' and unit 'u'
    """
    missing_keys = []
    if isinstance(dataset, int):
        dataset = show_num(dataset, do_plot=False)
    snapshot = dataset.snapshot()
    meta_dict = defaultdict(dict)
    for instr, param in specific_list or get_metadata_list():
        try:
            unit = _getFromDict(snapshot, ["station",
                                           "instruments",
                                           instr,
                                           "parameters",
                                           param,
                                           "unit"])
            value = _getFromDict(snapshot, ["station",
                                            "instruments",
                                            instr,
                                            "parameters",
                                            param,
                                            "value"])
            meta_dict[instr][param] = {}
            meta_dict[instr][param]['value'] = value
            meta_dict[instr][param]['unit'] = unit
        except KeyError:
            missing_keys.append([instr, param])
    if printout:
        _print_metadata(meta_dict)
        _ = _get_data_duration(dataset)
    if len(missing_keys) > 0:
        print('\nSome of the specified parameters were not found in the '
              'snapshot metadata for this dataset:')
        for missing in missing_keys:
            print(missing[0] + ' ' + missing[1])
    return meta_dict


def _get_data_duration(dataset):
    """
    Function which gets the duration a dataset took to complete

    Args:
        dataset (qcodes dataset)

    Returns:
        duration in seconds
    """
    if 'loop' in dataset.metadata.keys():
        start = parser.parse(dataset.metadata['loop']['ts_start'])
        try:
            end = parser.parse(dataset.metadata['loop']['ts_end'])
        except KeyError:
            print('Cannot get data_duration: no ts_end, loop was probably '
                  'stopped by KeyboardInterrupt')
            return
    elif 'measurement' in dataset.metadata.keys():
        start = parser.parse(dataset.metadata['measurement']['ts_start'])
        try:
            end = parser.parse(dataset.metadata['measurement']['ts_end'])
        except KeyError:
            print('Cannot get data_duration: no ts_end, measurement was '
                  'probably stopped by KeyboardInterrupt')
            return
    else:
        print('Cannot get data_duration: could not find "loop" or '
              '"measurement" in dataset.metadata.keys()')
        return
    dur = end - start
    m, s = divmod(dur.total_seconds(), 60)
    h, m = divmod(m, 60)
    print("data taking duration %d:%02d:%02d" % (h, m, s))
    return dur.total_seconds()


def _getFromDict(dataDict, mapList):
    """
    Basic helper function which given a mapList (list) as a path gets the value
    from dataDict (nested dictionary structure)
    """
    return reduce(operator.getitem, mapList, dataDict)


def _print_metadata(meta_dict):
    """
    Function which given a metadata dictionary generated by get_metadata
    prints it.
    """
    for instr in meta_dict:
        print(instr)
        for param in meta_dict[instr]:
            print('\t{} : {} {}'.format(param,
                                        meta_dict[instr][param]['value'],
                                        meta_dict[instr][param]['unit']))
