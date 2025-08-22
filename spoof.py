import numpy as np
import matplotlib.pyplot as plt
import time

import SoapySDR
from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32

def hackrf_open(fs=20_000_000, fc=2_457_000_000, lna=40, vga=20, bw=None, amp=False):
    sdr = SoapySDR.Device(dict(driver="hackrf"))
    sdr.setSampleRate(SOAPY_SDR_RX, 0, fs)
    sdr.setFrequency(SOAPY_SDR_RX, 0, fc)
    if bw is None: bw = fs
    try: sdr.setBandwidth(SOAPY_SDR_RX, 0, bw)
    except: pass
    try:
        sdr.setGain(SOAPY_SDR_RX, 0, "LNA", int(lna))
        sdr.setGain(SOAPY_SDR_RX, 0, "VGA", int(vga))
    except: pass
    try: sdr.writeSetting("AMP", "true" if amp else "false")
    except: pass
    rx = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
    sdr.activateStream(rx)
    return sdr, rx

def capture_psd(sdr, rx, fc, fs, nfft=4096, avg_frames=32):
    """Επιστρέφει (freqs_Hz, psd_dB) γύρω από fc."""
    window = np.hanning(nfft).astype(np.float32)
    den = np.sum(window**2)
    acc = None
    frames = 0
    while frames < avg_frames:
        buf = np.empty(nfft, np.complex64)
        sr = sdr.readStream(rx, [buf], nfft)
        if not hasattr(sr, "ret") or sr.ret != nfft:
            continue
        x = buf * window
        spec = np.fft.fftshift(np.fft.fft(x))
        psd = (np.abs(spec)**2) / den
        acc = psd if acc is None else acc + psd
        frames += 1
    psd_avg = acc / max(frames, 1)
    psd_db = 10*np.log10(psd_avg + 1e-12)
    freqs = np.fft.fftshift(np.fft.fftfreq(nfft, 1/fs)) + fc
    return freqs, psd_db

def channel_power(freqs, psd_db, center_hz, width_hz=20_000_000):
    """Ολοκλήρωση ισχύος σε ζώνη (π.χ. 20 MHz Wi-Fi) γύρω από center_hz."""
    mask = (freqs >= center_hz - width_hz/2) & (freqs <= center_hz + width_hz/2)
    # άθροισμα στο linear και μετατροπή σε dB
    p_lin = np.sum(10**(psd_db[mask]/10.0))
    return 10*np.log10(p_lin + 1e-20)

def scan_wifi_24GHz(sdr, rx, fs, nfft=4096, avg_frames=16):
    """Μετρά ισχύ σε CH1–13 (2.4 GHz). Επιστρέφει dict {ch: power_dB}."""
    # Κέντρα καναλιών 2.4 GHz, 5 MHz spacing, κανάλι 1=2412 MHz
    ch_to_fc = {ch: (2_400_000_000 + 5_000_000*(ch-1) + 12_000_000) for ch in range(1,14)}
    results = {}
    for ch, fc in ch_to_fc.items():
        sdr.setFrequency(SOAPY_SDR_RX, 0, fc)
        # μικρό ζέσταμα buffer
        _ = sdr.readStream(rx, [np.empty(nfft, np.complex64)], nfft)
        freqs, psd_db = capture_psd(sdr, rx, fc, fs, nfft=nfft, avg_frames=avg_frames)
        pw = channel_power(freqs, psd_db, center_hz=fc, width_hz=20_000_000)
        results[ch] = pw
    return results

def plot_psd(freqs, psd_db, title="Spectrum"):
    plt.figure()
    plt.plot(freqs/1e6, psd_db)
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("PSD (dB, uncalibrated)")
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # ---- ΡΥΘΜΙΣΕΙΣ RX ----
    FS   = 20_000_000    # Προτείνεται 20 MS/s για Wi-Fi (ελάχιστο ~10–12.5)
    FC   = 2_457_000_000 # Κανάλι 1 (2.412 GHz)
    LNA  = 40
    VGA  = 20
    NFFT = 4096
    AVG  = 32

    sdr, rx = hackrf_open(fs=FS, fc=FC, lna=LNA, vga=VGA, bw=FS, amp=False)
    try:
        # 1) ΜΕΤΡΗΣΗ/ΠΛΟΤ γύρω από ένα κανάλι
        freqs, psd_db = capture_psd(sdr, rx, FC, FS, nfft=NFFT, avg_frames=AVG)
        plot_psd(freqs, psd_db, title=f"Wi-Fi around {FC/1e6:.3f} MHz | fs={FS/1e6:.1f} MS/s")

        # 2) (Προαιρετικό) Σάρωση ισχύος ανά κανάλι 1–13
        results = scan_wifi_24GHz(sdr, rx, fs=FS, nfft=NFFT, avg_frames=16)
        print("Channel power (approx., dB):")
        for ch in sorted(results):
            print(f"CH{ch:2d} @ {2412 + 5*(ch-1)} MHz : {results[ch]:6.1f} dB")

    finally:
        try: sdr.deactivateStream(rx)
        except: pass
        try: sdr.closeStream(rx)
        except: pass
