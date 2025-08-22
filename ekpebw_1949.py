import numpy as np
def run_hackrf_tx(
    fc=2412177300,      # Κεντρική συχνότητα (Hz)
    fs=1e6,             # Sample rate
    lna_gain=0,         # LNA gain (δεν χρησιμοποιείται στο TX)
    vga_gain=20,        # VGA gain (TX gain)
    bw=None,            # Bandwidth
    chunk_size=8192,    # Μέγεθος chunk
    duration_min=1000     # Διάρκεια εκπομπής σε δευτερόλεπτα
):
    try:
        import SoapySDR
        from SoapySDR import SOAPY_SDR_TX, SOAPY_SDR_CF32
    except Exception as e:
       ## print("Πρόβλημα: Δεν βρέθηκε το SoapySDR για Python. Εγκατάσταση: pip install SoapySDR")
      raise

    args = dict(driver="hackrf")
    sdr = SoapySDR.Device(args)

    sdr.setSampleRate(SOAPY_SDR_TX, 0, fs)
    sdr.setFrequency(SOAPY_SDR_TX, 0, fc)
    if bw is not None:
        sdr.setBandwidth(SOAPY_SDR_TX, 0, bw)
    try:
        sdr.setGain(SOAPY_SDR_TX, 0, "VGA", vga_gain)
    except Exception:
        pass

    txStream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
    sdr.activateStream(txStream)

    # Παράδειγμα: εκπομπή συνεχούς carrier (complex sinusoid)
    t = np.arange(chunk_size) / fs
    iq_chunk = np.exp(1j * 2 * np.pi * 0 * t).astype(np.complex64)  # 0 Hz offset (carrier)

    print(f"Ξεκίνησε εκπομπή: fc={fc} Hz, fs={fs} Hz, chunk={chunk_size}")
    import time
    start_time = time.time()
    try:
        # Εκπομπή χωρίς χρονικό περιορισμό
        while True:
            ret = sdr.writeStream(txStream, [iq_chunk], len(iq_chunk))
            if hasattr(ret, "ret") and ret.ret < 0:
                print("TX error:", ret)
# ...existing code...
    finally:
        try:
            sdr.deactivateStream(txStream)
        except Exception:
            pass
        try:
            sdr.closeStream(txStream)
        except Exception:
            pass
    print("Τέλος εκπομπής.")

# ========== main ==========
if __name__ == "__main__":
    # Για εκπομπή στην 2412177300 Hz
    run_hackrf_tx(
        fc=2412177300,
        fs=1e6,
        vga_gain=20,
        chunk_size=8192,
        duration_min=1000  # 10 δευτερόλεπτα εκπομπής
    )