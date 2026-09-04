#!/bin/bash

# Detect OpenSSL from Homebrew (supports openssl@3 and openssl@1.1, x86_64 and ARM paths)
for ssl in /usr/local/opt/openssl@3 /opt/homebrew/opt/openssl@3 /usr/local/opt/openssl@1.1 /opt/homebrew/opt/openssl@1.1 /usr/local/Cellar/openssl@3 /opt/homebrew/Cellar/openssl@3; do
	if [ -d "$ssl/include" ]; then
		export CPATH=$CPATH:$ssl/include
		export LIBRARY_PATH=$LIBRARY_PATH:$ssl/lib
		echo "Using OpenSSL from: $ssl"
		break
	fi
done

VERSION=$(head -n 1 .qmake.conf)
VERSION=${VERSION:8}
VERSION_MAJOR=$(echo $VERSION | sed 's/\..*//')
. .ci/common/build.sh macos

mkdir -p ${app_name}.app/Contents/Frameworks
for f in libopentyper-*.dylib; do
	install_name_tool -change $f @rpath/$f \
		${app_name}.app/Contents/MacOS/${executable_name}
done
mv *.dylib ${app_name}.app/Contents/Frameworks/
macdeployqt ${app_name}.app -qmldir=src

npm install -g appdmg
mv ${app_name}.app res/macos-release/
appdmg res/macos-release/open-typer.json ${app_name}.dmg
