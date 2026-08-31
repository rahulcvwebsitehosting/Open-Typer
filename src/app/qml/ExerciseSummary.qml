/*
 * ExerciseSummary.qml
 * This file is part of Open-Typer
 *
 * Copyright (C) 2022-2023 - Rahul Shyam
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
import QtQuick.Controls.Material 2.5
import QtQuick.Layouts 1.12
import OpenTyper.Ui 1.0
import OpenTyper.UiComponents 1.0
import OpenTyper.Validator 1.0
import OpenTyper.Grades 1.0
import OpenTyper.Global 1.0

Rectangle {
	property int padding: 10
	property int fontPointSize: 14
	property ExerciseValidator validator: null
	property int totalTime
	property int totalHits
	property int netHits
	property int grossHits
	property int mistakes
	property real accuracy
	readonly property string grade: validator == null ? "" : gradeCalc.grade
	height: columnLayout.implicitHeight + padding * 2
	radius: 10
	color: ThemeEngine.panelColor
	border.color: ThemeEngine.borderColor
	clip: true
	onValidatorChanged: {
		resetClass();
		updateGrade();
	}

	function resetClass() {
		classComboBox.currentIndex = Settings.getValue("grades", "selectedClass") + 1;
	}

	function updateGrade() {
		if(validator == null)
			return;
		gradeCalc.validator = validator;
		gradeCalc.targetHitsPerMinute = ClassManager.targetHitsPerMinute(classComboBox.currentIndex - 1);
	}

	GradeCalculator {
		id: gradeCalc
	}

	ColumnLayout {
		id: columnLayout
		x: padding
		y: padding

		RowLayout {
			Layout.fillWidth: true
			Label {
				text: qsTr("Total time:")
				font.bold: true
				font.pointSize: fontPointSize
			}
			Label {
				text: getTime(totalTime)
				font.pointSize: fontPointSize
				function getTime(time) {
					var minutes = Math.floor(time / 60);
					var seconds = time % 60;
					var out = "";
					if(minutes > 0)
						out += minutes + " min ";
					if((seconds > 0) || (minutes + seconds == 0))
						out += seconds + " s";
					return out;
				}
			}
		}

		RowLayout {
			Layout.fillWidth: true
			Label {
				text: qsTr("Total number of hits:")
				font.bold: true
				font.pointSize: fontPointSize
			}
			Label {
				text: totalHits
				font.pointSize: fontPointSize
			}
		}

		RowLayout {
			Layout.fillWidth: true
			Label {
				text: qsTr("Number of net hits per minute:")
				font.bold: true
				font.pointSize: fontPointSize
			}
			Label {
				text: netHits
				font.pointSize: fontPointSize
			}
		}

		RowLayout {
			Layout.fillWidth: true
			Label {
				text: qsTr("Number of gross hits per minute:")
				font.bold: true
				font.pointSize: fontPointSize
			}
			Label {
				text: grossHits
				font.pointSize: fontPointSize
			}
		}

		RowLayout {
			Layout.fillWidth: true
			Label {
				text: qsTr("Mistakes:")
				font.bold: true
				font.pointSize: fontPointSize
			}
			Label {
				text: mistakes
				font.pointSize: fontPointSize
			}
		}

		RowLayout {
			Layout.fillWidth: true
			Label {
				text: qsTr("Accuracy:")
				font.bold: true
				font.pointSize: fontPointSize
			}
			Label {
				text: Math.floor(accuracy * 10000) / 100 + " %"
				font.pointSize: fontPointSize
			}
		}

		RowLayout {
			Layout.fillWidth: true
			visible: classComboBox.model.length > 1
			Label {
				text: qsTr("Class:")
				font.bold: true
				font.pointSize: fontPointSize
			}
			CustomComboBox {
				id: classComboBox
				model: {
					let arr1 = [qsTr("No class selected")];
					let arr2 = ClassManager.classNames;
					return arr1.concat(arr2);
				}
				currentIndex: Settings.getValue("grades", "selectedClass") + 1
				onCurrentIndexChanged: updateGrade()
			}
		}

		RowLayout {
			Layout.fillWidth: true
			Label {
				text: qsTr("Grade:")
				font.bold: true
				font.pointSize: fontPointSize
			}
			Label {
				text: validator == null ? "" : gradeCalc.grade
				font.pointSize: fontPointSize
			}
		}

		// ── Smart Analysis — isolated (no timed-para conflict) ──
		Rectangle {
			Layout.fillWidth: true
			Layout.topMargin: 12
			height: smartCol.implicitHeight + 16
			radius: 8
			color: "#eff6ff"
			border.color: "#bfdbfe"
			visible: validator !== null
			ColumnLayout {
				id: smartCol
				anchors.fill: parent
				anchors.margins: 8
				spacing: 6
				RowLayout {
					Layout.fillWidth: true
					Label { text: qsTr("🧠 Smart Analysis"); font.bold:true; color:"#0f172a" }
					Item { Layout.fillWidth:true }
					AccentButton {
						text: qsTr("Open Smart Analysis")
						font.pointSize: 9
						onClicked: smartAnalyzerDialog.open()
					}
				}
				Label {
					Layout.fillWidth: true
					wrapMode: Text.WordWrap
					font.pointSize: 9
					color: "#334155"
					text: {
						if(validator===null) return ""
						// trigger via SmartAnalyzer if available, otherwise fallback hint
						return qsTr("Tap to see which letters you miss, why (adjacent keys / Shift / transposition), and get a personalized drill.")
					}
				}
			}
		}

		SmartAnalyzer { id: smartAnalyzer }
		Loader {
			id: smartAnalyzerDialogLoader
			active: false
			sourceComponent: Component {
				SmartAnalysisDialog {
					targetText: validator ? validator.exerciseText : ""
					typedText: validator ? validator.inputText : ""
					elapsedSec: totalTime
					onLoadDrill: {
						// Home.qml will handle loadText via signal; for now just log
						console.log("Smart drill:", drillText.substring(0,60))
					}
				}
			}
		}
		// dialog opener helper
		QtObject {
			id: smartAnalyzerDialog
			function open(){
				if(validator===null) return
				// lazy create Dialog if not exists — use dynamic creation
				let comp = Qt.createComponent("dialogs/SmartAnalysisDialog.qml")
				if(comp.status===Component.Ready){
					let dlg = comp.createObject(columnLayout, {"targetText": validator.exerciseText, "typedText": validator.inputText, "elapsedSec": totalTime})
					if(dlg){
						dlg.onLoadDrill.connect(function(drill){
							// bubble to parent Home via custom signal? For now copy to clipboard
							// Home.qml can listen via Connections if needed
							if(typeof loadText !== "undefined") loadText(drill, false)
						})
						dlg.open()
					}
				}
			}
		}
	}
}
