import time
import numpy as np
from SoapySDR import Device, SOAPY_SDR_TX, SOAPY_SDR_CF32

def tx_noise_block(fc, fs=20_000_000, bw=18_000_000,
                   vga_gain=30, amplitude=0.5, seconds=60, chunk_size=16384):
    sdr = Device(dict(driver="hackrf"))
    sdr.setSampleRate(SOAPY_SDR_TX, 0, fs)
    sdr.setFrequency(SOAPY_SDR_TX, 0, fc)
    try: sdr.setBandwidth(SOAPY_SDR_TX, 0, fs)
    except: pass
    sdr.setGain(SOAPY_SDR_TX, 0, "VGA", vga_gain)

    tx = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
    sdr.activateStream(tx)

    # band-limited noise
    N = 1 << 16
    X = (np.random.randn(N) + 1j*np.random.randn(N)).astype(np.complex64)
    freqs = np.fft.fftfreq(N, 1/fs)
    X[np.abs(freqs) > (bw/2)] = 0
    x = np.fft.ifft(X).astype(np.complex64)
    x /= np.max(np.abs(x))
    x *= amplitude

    print(f"TX noise at {fc/1e6:.3f} MHz | fs={fs/1e6} MS/s | BW≈{bw/1e6} MHz")
    t0 = time.time()
    idx = 0
    while time.time() - t0 < seconds:
        end = idx + chunk_size
        if end <= len(x):
            buf = x[idx:end]
            idx = end
        else:
            buf = np.concatenate([x[idx:], x[:end-len(x)]])
            idx = end - len(x)
        sdr.writeStream(tx, [buf.astype(np.complex64)], len(buf))

    sdr.deactivateStream(tx)
    sdr.closeStream(tx)
    print("Done TX.")

if __name__ == "__main__":
    # πρώτο μισό του καναλιού
    tx_noise_block(fc=2_452_000_000, seconds=60)
    # δεύτερο μισό του καναλιού
    tx_noise_block(fc=2_462_000_000, seconds=60)
