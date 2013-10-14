"""
@brief Unit tests for BrightPixels module.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
import os
import unittest
import numpy as np
import lsst.test_scripts.image_utils as imutils
import lsst.test_scripts.sensor as sensorTest
import lsst.test_scripts.sensor.sim_tools as sim_tools

class BrightPixelsTestCase(unittest.TestCase):
    """Test case for BrightPixels code."""
    def setUp(self):
        self.dark_file = 'bright_pixels_test.fits'
        self.emin = 10
        self.exptime = 10
        self.gain = 5
        self.ccdtemp = -100
        self.bias_level, self.bias_sigma = 1e2, 4
        self.dark_curr=2e-3
        self.ccd = sim_tools.CCD(exptime=self.exptime, gain=self.gain,
                                 ccdtemp=self.ccdtemp)
        self.ccd.add_bias(self.bias_level, self.bias_sigma)
        self.ccd.add_dark_current(level=self.dark_curr)
        self.nsig = ( (self.emin*self.exptime/self.gain)
                      /self.ccd.segments[imutils.allAmps[0]].sigma() )
        self.npix = 100
        self.pixels = self.ccd.generate_bright_pix(self.npix)
        self.ccd.add_bright_pix(self.pixels, nsig=self.nsig)
        self.ccd.writeto(self.dark_file)
        self.mask_file = 'bp_mask_file.fits'
    def tearDown(self):
        os.remove(self.dark_file)
        os.remove(self.mask_file)
    def test_generate_mask(self):
        ccd = sensorTest.MaskedCCD(self.dark_file)
        for amp in imutils.allAmps:
            bp = sensorTest.BrightPixels(ccd, amp, ccd.md.get('EXPTIME'),
                                         self.gain, ethresh=self.emin/2.,
                                         colthresh=100)
            results = bp.find()
            bp.generate_mask(self.mask_file)
            pixels = np.array(np.where(self.pixels[amp] == 1))
            pixels = pixels.transpose()
            pixels = [(x, y) for y, x in pixels]
            pixels.sort()
            self.assertEqual(pixels, results[0])

class BrightColumnsTestCase(unittest.TestCase):
    """Test case for BrightPixels code."""
    def setUp(self):
        self.dark_file = 'bright_columns_test.fits'
        self.emin = 10
        self.exptime = 10
        self.gain = 5
        self.ccdtemp = -100
        self.bias_level, self.bias_sigma = 1e2, 4
        self.dark_curr=2e-3
        self.ccd = sim_tools.CCD(exptime=self.exptime, gain=self.gain,
                                 ccdtemp=self.ccdtemp)
        self.ccd.add_bias(self.bias_level, self.bias_sigma)
        self.ccd.add_dark_current(level=self.dark_curr)
        self.nsig = ( (self.emin*self.exptime/self.gain)
                      /self.ccd.segments[imutils.allAmps[0]].sigma() )
        self.ncols = 10
        self.columns = self.ccd.generate_bright_cols(self.ncols)
        self.ccd.add_bright_cols(self.columns, nsig=self.nsig)
        self.ccd.writeto(self.dark_file)
        self.mask_file = 'bp_mask_file.fits'
    def tearDown(self):
        os.remove(self.dark_file)
        os.remove(self.mask_file)
    def test_generate_mask(self):
        ccd = sensorTest.MaskedCCD(self.dark_file)
        for amp in imutils.allAmps:
            bp = sensorTest.BrightPixels(ccd, amp, ccd.md.get('EXPTIME'),
                                         self.gain, ethresh=self.emin/2.,
                                         colthresh=100)
            results = bp.find()
            bp.generate_mask(self.mask_file)
            columns = sorted(self.columns[amp])
            self.assertEqual(columns, results[1])

if __name__ == '__main__':
    unittest.main()
