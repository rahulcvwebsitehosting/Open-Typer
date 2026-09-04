#!/bin/bash

if [[ "$1" != "1" ]]; then
	curl -o openssl.zip -LJO https://github.com/CristiFati/Prebuilt-Binaries/raw/master/OpenSSL/v3.0/OpenSSL-3.0.7-Win-pc064.zip
	mkdir -p ../openssl
	unzip openssl.zip -d ../openssl
	mkdir -p C:/OpenSSL
	# The archive may extract into a versioned directory (e.g. OpenSSL/OpenSSL/3.0.7)
	if [ -d ../openssl/OpenSSL/OpenSSL/3.0.7 ]; then
		mv ../openssl/OpenSSL/OpenSSL/3.0.7/* C:/OpenSSL
	elif [ -d ../openssl/OpenSSL/OpenSSL ]; then
		mv ../openssl/OpenSSL/OpenSSL/* C:/OpenSSL
	else
		mv ../openssl/* C:/OpenSSL
	fi
	rm openssl.zip
	find C:/OpenSSL/lib -depth -name "*.lib" -exec sh -c 'f="{}"; mv -- "$f" "${f%.lib}.a"' \;
else
	cd release
	cp C:/OpenSSL/bin/*.dll ./
	cd ..
fi
