"""PassSigner adapters.

`FakeSigner` — an empty signature, so dev/CI produce a structurally-valid
`.pkpass` (bundle layout, manifest, assets) without any certificate. The pass
won't be accepted by Apple Wallet, but the whole pipeline and the download
flow are exercisable.

`AppleP12Signer` — the real signer, in use. The Dion Apple Developer cert is in
place (team `AVN9H8BY3X`, pass type `pass.com.passly`) and `deps.py` switches to
this signer automatically when APPLE_CERT_P12 points at a file. `cryptography` is
imported lazily so dev/CI need neither it exercised nor the cert present.
"""

from __future__ import annotations


class FakeSigner:
    real = False

    def sign(self, manifest: bytes) -> bytes:  # noqa: ARG002
        return b""


class AppleP12Signer:
    """Signs manifest.json with the Pass Type ID cert, chained via Apple WWDR.

    Standard detached PKCS#7. **Verified end-to-end at P1 close:** the passes it
    signs add to Apple Wallet and the signature verifies against Apple WWDR.
    """

    real = True

    def __init__(self, p12_path: str, password: str, wwdr_path: str) -> None:
        self._p12_path = p12_path
        self._password = password
        self._wwdr_path = wwdr_path

    def sign(self, manifest: bytes) -> bytes:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            pkcs7,
            pkcs12,
        )
        from cryptography.x509 import load_der_x509_certificate, load_pem_x509_certificate

        with open(self._p12_path, "rb") as fh:
            key, cert, _ = pkcs12.load_key_and_certificates(
                fh.read(), self._password.encode() or None
            )
        with open(self._wwdr_path, "rb") as fh:
            raw = fh.read()
        wwdr = (
            load_pem_x509_certificate(raw)
            if b"-----BEGIN" in raw
            else load_der_x509_certificate(raw)
        )

        return (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(manifest)
            .add_signer(cert, key, hashes.SHA256())
            .add_certificate(wwdr)
            .sign(Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature])
        )
