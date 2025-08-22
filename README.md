TX (Transmit) → εκπομπή

Δημιουργείς stream με
{python script:
sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
}
Στέλνεις δείγματα (complex I/Q) με sdr.writeStream(...).

Άρα TX = πομπός, εκπέμπεις σήμα στην κεραία του HackRF.





RX (Receive) → λήψη

Δημιουργείς stream με
python script:
sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
Διαβάζεις δείγματα με sdr.readStream(...).

Άρα RX = δέκτης, λαμβάνεις σήματα από την κεραία.
