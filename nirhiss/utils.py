import numpy as np
from tqdm import tqdm
from astropy.table import Table
import transitspectroscopy as ts

__all__ = ['scaling_image_regions', 'bin_at_resolution', 'chromatic_writer',
           'exotep_to_ers_format', 'get_MAD_sigma']

def scaling_image_regions(integraions, bkg, x1, x2, y1, y2,
                          vals=np.linspace(0,10,500), test=True):
    """
    Scales a given (x1, y1) to (x2, y2) region of the input integration
    to the input background. This function is meant to be used for scaling the
    STScI model background and the F277W regions to the raw Stage 2
    integrations.

    Parameters
    ----------
    integrations : np.ndarray
       The data frames to scale the background to.
    bkg : np.ndarray
       The background model to use.
    x1 : int
       The lower left x-coordinate of the region to scale.
    x2 : int
       The upper right x-coordinate of the region to scale.
    y1 : int
       The lower left y-coordinate of the region to scale.
    y2 : int
       The upper right y-coordinate of the region to scale.
    vals : np.array, optional
       The scaling values to test over. Default is `np.linspace(0,10,500)`.
       I recommend running this with `test = True` first, and then changing this
       vals array to be centered on the best fit from the test round.
    test : bool, optional
       The option to test values first before running the whole scaling routine.
       Default is `True`. If `True`, will only run the first five integrations
       and print the scaling values from that run.

    Returns
    -------
    scaling_val : float
       The median best-fit scaling value from the background to the integration.
    """

    shape = (x2-x1) * (y2-y1)
    scaling_vals = np.zeros(len(integrations))

    if test:
        length = 5
    else:
        length=len(integrations)

    for j in tqdm(range(length)):
        rms = np.zeros(len(vals))

        for i, v in enumerate(vals):
            diff = integrations[j][x1:x2,y1:y2] - (bkg[x1:x2,y1:y2]*v)
            rms[i] = np.sqrt(np.nansum(diff**2)/shape)

        scaling_vals[j] = vals[np.argmin(rms)]

    if test:
        print(scaling_vals[:5])

    return np.nanmedian(scaling_vals)


def chromatic_writer(filename, time, wavelength, flux, var):
    """Writes numpy files to read into chromatic reader for `feinstein.py`."""
    np.save(filename+'.npy', [time, wavelength, flux, var])
    return


def exotep_to_ers_format(filename1, filename2, filename):
    """
    Takes the outputs of exotep and puts it in the agreed upon format.

    Parameters
    ----------
    filename1 : str
       The filename (+ path) for the output csv for NIRISS order 1.
    filename2 : str
       The filename (+ path) for the output csv for NIRISS order 2.
    filename : str
       The output filename to save the new table to.

    Returns
    -------
    tab : astropy.table.Table
    """
    table1 = Table.read(filename1, format='csv')
    table2 = Table.read(filename2, format='csv')

    tab = Table(names=['wave', 'wave_err', 'dppm', 'dppm_err', 'order'],
                dtype=[np.float64, np.float64, np.float64, np.float64, int])

    for i in range(len(table1)):
        row = [table1['wave'][i], table1['waveMin'][i],
               table1['yval'][i], table1['yerrLow'][i], 1]
        tab.add_row(row)

    short = table2[table2['wave'] < 0.9]
    for i in range(len(short)):
        row = [short['wave'][i], short['waveMin'][i],
               short['yval'][i], short['yerrLow'][i], 2]
        tab.add_row(row)

    tab.write(filename, format='csv', overwrite=True)
    return tab

def bin_at_resolution(wavelengths, depths, R=100, method='median'):
    """
    A wrapper for `transitspectroscopy.utils.bin_at_resoluion`.

    Parameters
    ----------
    wavelengths : np.array
        Array of wavelengths
    depths : np.array
        Array of depths at each wavelength.
    R : int
        Target resolution at which to bin (default is 100)
    method : string
        'mean' will calculate resolution via the mean --- 'median' via the
        median resolution of all points in a bin.

    Returns
    -------
    wout : np.array
        Wavelength of the given bin at resolution R.
    dout : np.array
        Depth of the bin.
    derrout : np.array
        Error on depth of the bin.
    """
    outputs = ts.utils.bin_at_resolution(wavelength, depths, R=R, method=method)
    return outputs[0], outputs[1], outputs[2]

def get_MAD_sigma(x, median):
    """
    Wrapper function for transitspectroscopy.utils.get_MAD_sigma to estimate
    the noise properties of the light curves.

    Parameters
    ----------
    x : np.ndarray
    median : np.ndarray
    """
    mad = ts.utils.get_mad_sigma(x, median)
