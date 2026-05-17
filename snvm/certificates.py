import os
import ssl


def apply_certifi_environment() -> None:
    apply_system_truststore()
    cafile = certifi_cafile()
    if not cafile:
        return

    os.environ.setdefault("SSL_CERT_FILE", cafile)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", cafile)


def certifi_ssl_context() -> ssl.SSLContext | None:
    apply_system_truststore()
    cafile = certifi_cafile()
    if not cafile:
        return None
    return ssl.create_default_context(cafile=cafile)


def apply_system_truststore() -> None:
    try:
        import truststore
    except ImportError:
        return
    truststore.inject_into_ssl()


def certifi_cafile() -> str | None:
    try:
        import certifi
    except ImportError:
        return None
    return certifi.where()
