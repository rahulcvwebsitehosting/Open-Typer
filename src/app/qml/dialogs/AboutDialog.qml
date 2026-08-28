/*
 * AboutDialog.qml
 * This file is part of Open-Typer
 *
 * Copyright (C) 2023 - Rahul Shyam
 *
 * Open-Typer is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * Open-Typer is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Open-Typer. If not, see <http://www.gnu.org/licenses/>.
 */

import QtQuick 2.12
import QtQuick.Controls 2.5
import QtQuick.Layouts 1.12
import OpenTyper.Ui 1.0
import OpenTyper.UiComponents 1.0

CustomDialog {
	//: For example "About Open-Typer" (%1 is the app name)
	title: qsTr("About %1").arg(Qt.application.displayName)
	standardButtons: Dialog.Ok

	contentItem: RowLayout {
		spacing: 25

		Image {
			source: "qrc:/res/images/icon.ico"
			sourceSize.width: 60
			sourceSize.height: 60
			Layout.alignment: Qt.AlignTop
		}

		ColumnLayout {
			Label {
				text: Qt.application.displayName
				font.bold: true
			}

			Label {}

			Label {
				text: qsTr("Version: %1").arg(Qt.application.version)
			}

			Label {
				text: qsTr("Revision: %1").arg(QmlUtils.applicationRevision())
			}

			Label {
				readonly property string src: "https://github.com/rahulcvwebsitehosting/Open-Typer"
				text: qsTr("Source code: %1").arg("<a href=\"" + src + "\">" + src + "</a>")
				onLinkActivated: Qt.openUrlExternally(link)
			}

			Label {}

			Label {
				text: "Copyright © 2021-" + QmlUtils.applicationBuildYear() + " Rahul Shyam"
			}

			Label {
				text: qsTr("Published with the GNU General Public License.")
			}

			Label {}

			Label {
				readonly property string portfolio: "https://rahulshyam-portfolio.vercel.app/"
				text: qsTr("Designed & developed by %1").arg("<a href=\"" + portfolio + "\">Rahul S</a>")
				onLinkActivated: Qt.openUrlExternally(link)
			}

			Label {
				readonly property string githubProfile: "https://github.com/rahulcvwebsitehosting"
				text: qsTr("GitHub: %1").arg("<a href=\"" + githubProfile + "\">" + githubProfile + "</a>")
				onLinkActivated: Qt.openUrlExternally(link)
			}

			Label {
				readonly property string emailAddr: "mailto:rahulshyamcv@gmail.com"
				text: qsTr("Email: %1").arg("<a href=\"" + emailAddr + "\">rahulshyamcv@gmail.com</a>")
				onLinkActivated: Qt.openUrlExternally(link)
			}

			Label {
				readonly property string phoneUrl: "https://wa.me/917305169964"
				text: qsTr("Phone: %1").arg("<a href=\"" + phoneUrl + "\">+91 73051 69964</a>")
				onLinkActivated: Qt.openUrlExternally(link)
			}

			Label {
				readonly property string linkedin: "https://www.linkedin.com/in/rahulshyamcivil/"
				readonly property string xUrl: "https://x.com/RahulShyamCv"
				readonly property string instagram: "https://www.instagram.com/rahulcvjps/"
				readonly property string threads: "https://www.threads.net/@RahulCvJPS"
				text: "<a href=\"" + linkedin + "\">LinkedIn</a> · <a href=\"" + xUrl + "\">X @RahulShyamCv</a> · <a href=\"" + instagram + "\">Instagram @rahulcvjps</a> · <a href=\"" + threads + "\">Threads @rahulcvjps</a>"
				onLinkActivated: Qt.openUrlExternally(link)
			}
		}
	}
}
