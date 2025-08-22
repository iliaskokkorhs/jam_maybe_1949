import numpy as np
import matplotlib.pyplot as plt
import SoapySDR
from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32

def scan_spectrum(fc=2412177300, fs=1e6, chunk_size=65536):
    args = dict(driver="hackrf")
    sdr = SoapySDR.Device(args)
    sdr.setSampleRate(SOAPY_SDR_RX, 0, fs)
    sdr.setFrequency(SOAPY_SDR_RX, 0, fc)
    rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
    sdr.activateStream(rxStream)
    buff = np.empty(chunk_size, np.complex64)
    sr = sdr.readStream(rxStream, [buff], chunk_size)
    sdr.deactivateStream(rxStream)
    sdr.closeStream(rxStream)
    # Υπολογισμός φάσματος
    spectrum = np.abs(np.fft.fftshift(np.fft.fft(buff)))
    freqs = np.fft.fftshift(np.fft.fftfreq(chunk_size, 1/fs)) + fc
    plt.plot(freqs, 20*np.log10(spectrum))
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Power (dB)")
    plt.title("RF Spectrum around {:.0f} Hz".format(fc))
    plt.show()

if __name__ == "__main__":
    scan_spectrum()