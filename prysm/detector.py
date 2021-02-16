"""Detector-related simulations."""

from .mathops import np
from .mathops import is_odd


def olpf_ft(fx, fy, width_x, width_y):
    """Analytic FT of an optical low-pass filter, two or four pole.

    Parameters
    ----------
    fx : `numpy.ndarray`
        x spatial frequency, in cycles per micron
    fy : `numpy.ndarray`
        y spatial frequency, in cycles per micron
    width_x : `float`
        x diameter of the pixel, in microns
    width_y : `float`
        y diameter of the pixel, in microns

    Returns
    -------
    `numpy.ndarray`
        FT of the OLPF

    """
    return np.cos(2 * width_x * fx) * np.cos(2 * width_y * fy)


def pixel_ft(fx, fy, width_x, width_y):
    """Analytic FT of a rectangular pixel aperture.

    Parameters
    ----------
    fx : `numpy.ndarray`
        x spatial frequency, in cycles per micron
    fy : `numpy.ndarray`
        y spatial frequency, in cycles per micron
    width_x : `float`
        x diameter of the pixel, in microns
    width_y : `float`
        y diameter of the pixel, in microns

    Returns
    -------
    `numpy.ndarray`
        FT of the pixel

    """
    return np.sinc(fx * width_x) * np.sinc(fy * width_y)


def pixel(x, y, width_x, width_y):
    """Spatial representation of a pixel.

    Parameters
    ----------
    x : `numpy.ndarray`
        x coordinates
    y : `numpy.ndarray`
        y coordinates
    width_x : `float`
        x diameter of the pixel, in microns
    width_y : `float`
        y diameter of the pixel, in microns

    Returns
    -------
    `numpy.ndarray`
        spatial representation of the pixel

    """
    return x < width_x & x > -width_x & y < width_y & y > -width_y


def bindown(array, nsamples_x, nsamples_y=None, mode='avg'):
    """Bin (resample) an array.

    Parameters
    ----------
    array : `numpy.ndarray`
        array of values
    nsamples_x : `int`
        number of samples in x axis to bin by
    nsamples_y : `int`
        number of samples in y axis to bin by.  If None, duplicates value from nsamples_x
    mode : `str`, {'avg', 'sum'}
        sum or avg, how to adjust the output signal

    Returns
    -------
    `numpy.ndarray`
        ndarray binned by given number of samples

    Notes
    -----
    Array should be 2D.  TODO: patch to allow 3D data.

    If the size of `array` is not evenly divisible by the number of samples,
    the algorithm will trim around the border of the array.  If the trim
    length is odd, one extra sample will be lost on the left side as opposed
    to the right side.

    Raises
    ------
    ValueError
        invalid mode

    """
    if nsamples_y is None:
        nsamples_y = nsamples_x

    if nsamples_x == 1 and nsamples_y == 1:
        return array

    # determine amount we need to trim the array
    samples_x, samples_y = array.shape
    total_samples_x = samples_x // nsamples_x
    total_samples_y = samples_y // nsamples_y
    final_idx_x = total_samples_x * nsamples_x
    final_idx_y = total_samples_y * nsamples_y

    residual_x = int(samples_x - final_idx_x)
    residual_y = int(samples_y - final_idx_y)

    # if the amount to trim is symmetric, trim symmetrically.
    if not is_odd(residual_x) and not is_odd(residual_y):
        samples_to_trim_x = residual_x // 2
        samples_to_trim_y = residual_y // 2
        trimmed_data = array[samples_to_trim_x:final_idx_x + samples_to_trim_x,
                             samples_to_trim_y:final_idx_y + samples_to_trim_y]
    # if not, trim more on the left.
    else:
        samples_tmp_x = (samples_x - final_idx_x) // 2
        samples_tmp_y = (samples_y - final_idx_y) // 2
        samples_top = int(np.floor(samples_tmp_y))
        samples_bottom = int(np.ceil(samples_tmp_y))
        samples_left = int(np.ceil(samples_tmp_x))
        samples_right = int(np.floor(samples_tmp_x))
        trimmed_data = array[samples_left:final_idx_x + samples_right,
                             samples_bottom:final_idx_y + samples_top]

    intermediate_view = trimmed_data.reshape(total_samples_x, nsamples_x,
                                             total_samples_y, nsamples_y)

    if mode.lower() in ('avg', 'average', 'mean'):
        output_data = intermediate_view.mean(axis=(1, 3))
    elif mode.lower() == 'sum':
        output_data = intermediate_view.sum(axis=(1, 3))
    else:
        raise ValueError('mode must be average of sum.')

    # trim as needed to make even number of samples.
    # TODO: allow work with images that are of odd dimensions
    px_x, px_y = output_data.shape
    trim_x, trim_y = 0, 0
    if is_odd(px_x):
        trim_x = 1
    if is_odd(px_y):
        trim_y = 1

    return output_data[:px_x - trim_x, :px_y - trim_y]


def bindown_with_units(px_x, px_y, source_spacing, source_data):
    """Perform bindown, returning unit axes and data.

    Parameters
    ----------
    px_x : `float`
        pixel pitch in the x direction, microns
    px_y : `float`
        pixel pitch in the y direction, microns
    source_spacing : `float`
        pixel pitch in the source data, microns
    source_data : `numpy.ndarray`
        ndarray of regularly spaced data

    Returns
    -------
    ux : `numpy.ndarray`
        1D array of sample coordinates in the x direction
    uy : `numpy.ndarray`
        1D array of sample coordinates in the y direction
    data : `numpy.ndarray`
        binned-down data

    """
    # we assume the pixels are bigger than the samples in the source
    spp_x = px_x / source_spacing
    spp_y = px_y / source_spacing
    if min(spp_x, spp_y) < 1:
        raise ValueError('Pixels smaller than samples, bindown not possible.')
    else:
        spp_x, spp_y = int(np.ceil(spp_x)), int(np.ceil(spp_y))

    data = bindown(source_data, spp_x, spp_y, 'avg')
    s = data.shape
    extx, exty = s[0] * px_x // 2, s[1] * px_y // 2
    ux, uy = np.arange(-extx, extx, px_x), np.arange(-exty, exty, px_y)
    return ux, uy, data
