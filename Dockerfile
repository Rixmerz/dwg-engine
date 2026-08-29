# DWG engine: ezdxf + ODA File Converter (write) in one image.
# A plugin user needs only Docker; every native lib lives here. No paid CAD.
FROM debian:bookworm-slim

# xvfb+xauth: the ODA converter is a Qt app with no offscreen plugin, so it runs
# under a virtual X display. The libxcb-* set is what the qxcb plugin dlopens at
# runtime (not caught by ldd of the main binary) and bookworm-slim omits.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip \
        curl ca-certificates \
        xvfb xauth fontconfig \
        libgl1 libglib2.0-0 libxkbcommon0 libdbus-1-3 \
        libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
        libxcb-render0 libxcb-render-util0 libxcb-shape0 libxcb-xkb1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages ezdxf

# ODA File Converter (free). Fetched at build so the repo stays light. The
# guestfiles URL 302s to a short-lived presigned S3 link; curl -L follows it.
RUN curl -fsSL -o /tmp/oda.deb \
      "https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_lnxX64_8.3dll_27.1.deb" \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/oda.deb \
    && rm -f /tmp/oda.deb && rm -rf /var/lib/apt/lists/*

COPY engine/ /engine/
RUN chmod +x /engine/dwgconv /engine/entrypoint
ENTRYPOINT ["/engine/entrypoint"]
