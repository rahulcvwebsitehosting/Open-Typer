#!/bin/bash

sudo ()
{
    [[ $EUID = 0 ]] || set -- command sudo "$@"
    "$@"
}

# Build
if [[ "$1" != "0" ]]; then
    .ci/common/build.sh linux || exit 1
fi

# Install build dependencies
sudo apt-get update &&
sudo apt install -y build-essential g++ pkg-config curl wget libpng-dev libjpeg-dev zsync desktop-file-utils libxcb-cursor0 patchelf || exit 1

# Download prebuilt linuxdeploy and plugins (AppImage releases)
LD_URL="https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous"
LDQT_URL="https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous"
LDAI_URL="https://github.com/linuxdeploy/linuxdeploy-plugin-appimage/releases/download/continuous"

case "$(arch)" in
    aarch64)
        LD_ARCH="aarch64"
        ;;
    armv7l|armv6l)
        LD_ARCH="armhf"
        ;;
    *)
        LD_ARCH="x86_64"
        ;;
esac

curl -L -o linuxdeploy "$LD_URL/linuxdeploy-$LD_ARCH.AppImage" &&
curl -L -o linuxdeploy-plugin-qt "$LDQT_URL/linuxdeploy-plugin-qt-$LD_ARCH.AppImage" &&
curl -L -o linuxdeploy-plugin-appimage "$LDAI_URL/linuxdeploy-plugin-appimage-$LD_ARCH.AppImage" &&
chmod +x linuxdeploy linuxdeploy-plugin-qt linuxdeploy-plugin-appimage || exit 1

export PATH=$PATH:~/.local/bin

# Build AppImage
export QML_SOURCES_PATHS=src &&
export EXTRA_QT_PLUGINS="svg;" &&
export LDAI_UPDATE_INFORMATION="${appimage_zsync_prefix}${app_name}*-${APPIMAGE_ARCH-$(arch)}.AppImage.zsync"
echo "AppImage update information: ${LDAI_UPDATE_INFORMATION}"

case "$(qmake -query QMAKE_XSPEC)" in
    linux-arm-gnueabi-g++)
        wget https://github.com/AppImage/AppImageKit/releases/download/continuous/runtime-armhf
        export ARCH=arm
        export LDAI_RUNTIME_FILE=runtime-armhf
        ;;
    linux-aarch64-gnu-g++)
        wget https://github.com/AppImage/AppImageKit/releases/download/continuous/runtime-aarch64
        export ARCH=arm_aarch64
        export LDAI_RUNTIME_FILE=runtime-aarch64
        ;;
esac

./linuxdeploy --appdir AppDir -e open-typer -i snap/gui/open-typer.png -d res/linux-release/usr/share/applications/open-typer-appimage.desktop --plugin qt --output appimage
