"""
@brief Tools to create simulated CCD segment exposures under ideal
conditions.  Darks, flats, Fe55, etc..
"""
import os

import numpy as np
import numpy.random as random

import pyfits

import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
import lsst.afw.display.ds9 as ds9
from fe55_yield import Fe55Yield

import image_utils as imutils

class SegmentExposure(object):
    def __init__(self, exptime=1, gain=5, ccd_temp=-100,
                 bbox=imutils.full_segment):
        self.exptime = exptime
        self.gain = gain
        self.fe55_yield = Fe55Yield(ccd_temp)
        self.image = afwImage.ImageF(bbox)
        self.imarr = self.image.Factory(self.image, imutils.imaging).getArray()
        self.ny, self.nx = self.imarr.shape
        self.npix = self.nx*self.ny
        self._sigma = -1
    def add_bias(self, level=1e4, sigma=4):
        """The parameters level and bias are in units of e- and
        converted on output to DN via the system gain."""
        fullarr = self.image.getArray()
        ny, nx = fullarr.shape
        bias_arr = np.array(random.normal(level, sigma, nx*ny),
                            dtype=np.float).reshape(ny, nx)
        fullarr += bias_arr/self.gain
    def add_dark_current(self, level=3):
        """Units of level should be e- per unit time and converted to
        DN on output."""
        dark_arr = self._poisson_imarr(level*self.exptime)/self.gain
        self.imarr += dark_arr
    def expose_flat(self, level):
        flat_arr = self._poisson_imarr(level*self.exptime)
        self.imarr += flat_arr
    def _poisson_imarr(self, level):
        return random.poisson(level, self.npix).reshape(self.ny, self.nx)
    def sigma(self):
        if self._sigma == -1:
            self._sigma = np.std(self.imarr)
        return self._sigma
    def add_bright_cols(self, ncols=1, nsig=5):
        bright_cols = np.arange(self.nx)
        random.shuffle(bright_cols)
        bright_cols = bright_cols[:ncols]
        for i in bright_cols:
            self.imarr[:, i] += nsig*self.sigma()
        return bright_cols
    def add_bright_pix(self, npix=100, nsig=5):
        bright_pix = np.concatenate((np.ones(npix), np.zeros(self.npix-npix)))
        random.shuffle(bright_pix)
        bright_pix = bright_pix.reshape(self.ny, self.nx)
        self.imarr += bright_pix*nsig*self.sigma()
        return np.where(bright_pix == 1)
    def add_Fe55_hits(self, nxrays=200, beta_frac=0.12):
        """Single pixel hits for now.  Need to investigate effects of
        charge diffusion."""
        ny, nx = self.imarr.shape
        for i in range(nxrays):
            x0 = random.randint(nx)
            y0 = random.randint(ny)
            if random.random() < beta_frac:
                signal = self.fe55_yield.beta()/self.gain
            else:
                signal = self.fe55_yield.alpha()/self.gain
            self.imarr[y0][x0] += int(signal)
                
def fitsFile(ccd_segments):
    output = pyfits.HDUList()
    output.append(pyfits.PrimaryHDU())
    output[0].header["EXPTIME"] = ccd_segments[0].exptime
    for amp, segment in zip(imutils.allAmps, ccd_segments):
        output.append(pyfits.ImageHDU(data=segment.image.getArray()))
        output[amp].name = 'AMP%s' % imutils.channelIds[amp]
        output[amp].header.update('DETSIZE', imutils.detsize)
        output[amp].header.update('DETSEC', imutils.detsec(amp))
    return output
                
def writeFits(ccd_segments, outfile, clobber=True):
    output = fitsFile(ccd_segments)
    if clobber:
        try:
            os.remove(outfile)
        except OSError:
            pass
    output.writeto(outfile)
    return outfile
    
def simulateDark(outfile, dark_curr, exptime=1, hdus=16, verbose=True):
    if verbose:
        print "simulating dark:", outfile
    segments = []
    for i in range(hdus):
        if verbose:
            print "HDU", i
        seg = SegmentExposure(exptime=exptime)
        seg.add_bias()
        seg.add_dark_current(dark_curr)
        segments.append(seg)
    writeFits(segments, outfile)

def simulateFlat(outfile, level, gain, dark_curr=1, exptime=1, hdus=16,
                 verbose=True):
    if verbose:
        print "simulating flat:", outfile
    segments = []
    for i in range(hdus):
        if verbose:
            print "HDU", i
        seg = SegmentExposure(exptime=exptime, gain=gain)
        seg.add_bias()
        seg.add_dark_current(dark_curr)
        seg.expose_flat(level)
        segments.append(seg)
    writeFits(segments, outfile)

if __name__ == '__main__':
    seg = SegmentExposure()
    
    seg.add_bias(1e4, 10)
    seg.add_dark_current(300)
    seg.expose_flat(200)
    cols = seg.add_bright_cols(ncols=1, nsig=5)
    pix = seg.add_bright_pix(npix=100, nsig=10)

    writeFits((seg,), 'test_image.fits')

#    ds9.mtv(exp.image)
