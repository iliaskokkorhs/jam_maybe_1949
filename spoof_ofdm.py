import time
import numpy as np
from SoapySDR import Device, SOAPY_SDR_TX, SOAPY_SDR_CF32

def make_ofdm_buffer(nfft=2048, ncarriers=1800, qpsk=True, amplitude=0.6,
                     cp_ratio=1/8, symbols_per_buffer=64):
    if qpsk:
        dibits = np.random.randint(0, 4, ncarriers)
        symbols = np.exp(1j * (np.pi/2 * dibits)).astype(np.complex64)
    else:
        bits = 2*np.random.randint(0, 2, ncarriers) - 1
        symbols = bits.astype(np.float32) + 0j

    X = np.zeros(nfft, dtype=np.complex64)
    half = ncarriers // 2
    X[nfft//2 - half : nfft//2 + half] = symbols[:2*half]

    x = np.fft.ifft(np.fft.ifftshift(X)).astype(np.complex64)
    x /= (np.max(np.abs(x)) + 1e-12)
    x *= amplitude

    cp_len = int(np.round(cp_ratio * nfft))
    if cp_len > 0:
        x = np.concatenate([x[-cp_len:], x])

    # φτιάξε μεγάλο buffer από πολλά σύμβολα
    buf = np.concatenate([x for _ in range(symbols_per_buffer)]).astype(np.complex64)
    return buf

def tx_ofdm_sweep(fc_list, dwell_s=60, total_time_s=60,
                  fs=20_000_000, vga_gain=32, chunk_size=16384):
    sdr = Device(dict(driver="hackrf"))
    sdr.setSampleRate(SOAPY_SDR_TX, 0, fs)
    try: sdr.setBandwidth(SOAPY_SDR_TX, 0, fs)
    except: pass
    try: sdr.setGain(SOAPY_SDR_TX, 0, "VGA", int(vga_gain))
    except: pass

    tx = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
    sdr.activateStream(tx)

    # buffer ~18 MHz occupied (ncarriers=1800 με fs=20e6, nfft=2048)
    x = make_ofdm_buffer(nfft=4096, ncarriers=3000, amplitude=0.8,
                         cp_ratio=1/8, symbols_per_buffer=128)

    print(f"Start sweep: fs={fs/1e6:.1f} MS/s, VGA={vga_gain} dB, dwell={dwell_s}s, total={total_time_s}s")
    t0 = time.time()
    try:
        while time.time() - t0 < total_time_s:
            for fc in fc_list:
                sdr.setFrequency(SOAPY_SDR_TX, 0, fc)
                t1 = time.time()
                idx = 0
                xlen = len(x)
                while time.time() - t1 < dwell_s and time.time() - t0 < total_time_s:
                    end = idx + chunk_size
                    if end <= xlen:
                        buf = x[idx:end]
                        idx = end
                    else:
                        buf = np.concatenate([x[idx:], x[:end-xlen]])
                        idx = end - xlen
                    ret = sdr.writeStream(tx, [buf], len(buf))
                    if hasattr(ret, "ret") and ret.ret < 0:
                        time.sleep(0.001)
    finally:
        try: sdr.deactivateStream(tx)
        except: pass
        try: sdr.closeStream(tx)
        except: pass
    print("Sweep done.")

if __name__ == "__main__":
    # CH10 @ 2457 MHz (40 MHz εύρος) -> δύο κέντρα:
    # χαμηλό μισό ~2452 MHz, υψηλό μισό ~2462 MHz
    fc_list = [2_452_000_000, 2_462_000_000]
    tx_ofdm_sweep(fc_list, dwell_s=60, total_time_s=60.0,
                  fs=20_000_000, vga_gain=32, chunk_size=16384)
