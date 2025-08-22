import numpy as np
import time

def run_hackrf_tx_wide_noise(
    fc=2_457_000_000,   # Hz
    fs=20_000_000,      # Hz (ψηλό για πλατύ φάσμα)
    tx_bw=18_000_000,   # επιθυμητό εύρος εκπομπής (<= fs)
    vga_gain=15,        # TX gain (ξεκίνα χαμηλά)
    amplitude=0.4,      # 0..1 – προσοχή να μη κλιπάρει
    chunk_size=16384,   # μέγεθος buffer προς writeStream
    seconds=60
):
    from SoapySDR import Device, SOAPY_SDR_TX, SOAPY_SDR_CF32

    # --- SDR setup
    sdr = Device(dict(driver="hackrf"))
    sdr.setSampleRate(SOAPY_SDR_TX, 0, fs)
    sdr.setFrequency(SOAPY_SDR_TX, 0, fc)
    try: sdr.setBandwidth(SOAPY_SDR_TX, 0, fs)
    except: pass
    try: sdr.setGain(SOAPY_SDR_TX, 0, "VGA", int(vga_gain))
    except: pass

    stx = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
    sdr.activateStream(stx)

    # --- Δημιουργία πλατιού baseband σήματος (band-limited complex noise)
    # Φτιάχνουμε μεγάλο block στο πεδίο συχνοτήτων και το φιλτράρουμε ορθογώνια
    N = 1 << 20  # 1,048,576 samples – αρκετό για να το “κυλάς”
    # θόρυβος στο freq domain (complex), zero-mean
    X = (np.random.randn(N) + 1j*np.random.randn(N)).astype(np.complex64)

    # συχνοτικά bins
    freqs = np.fft.fftfreq(N, d=1/fs)
    # μάσκα: κρατάμε μόνο |f| <= tx_bw/2
    mask = np.abs(freqs) <= (tx_bw/2)
    X[~mask] = 0

    # επιστροφή στο time domain
    x = np.fft.ifft(X).astype(np.complex64)
    # κανονικοποίηση ισχύος & amplitude
    x /= np.max(np.abs(x) + 1e-12)
    x *= amplitude

    print(f"TX wide noise @ {fc/1e6:.3f} MHz | fs={fs/1e6:.1f} MS/s | BW≈{tx_bw/1e6:.1f} MHz")

    # --- Streaming
    t0 = time.time()
    try:
        # στέλνουμε κυκλικά το buffer x
        idx = 0
        xlen = len(x)
        while time.time() - t0 < seconds:
            end = idx + chunk_size
            if end <= xlen:
                buf = x[idx:end]
                idx = end
            else:
                # wrap-around
                part1 = x[idx:]
                part2 = x[:end - xlen]
                buf = np.concatenate([part1, part2])
                idx = (end - xlen)
            ret = sdr.writeStream(stx, [buf.astype(np.complex64)], len(buf))
            # σε περίπτωση backpressure/underrun, μικρό sleep
            if hasattr(ret, "ret") and ret.ret < 0:
                time.sleep(0.001)
    finally:
        try: sdr.deactivateStream(stx)
        except: pass
        try: sdr.closeStream(stx)
        except: pass
    print("Τέλος εκπομπής.")

if __name__ == "__main__":
    run_hackrf_tx_wide_noise(
        fc=2_457_000_000,
        fs=20_000_000,
        tx_bw=18_000_000,
        vga_gain=10,      # ξεκίνα συντηρητικά
        amplitude=0.35,
        seconds=60
    )