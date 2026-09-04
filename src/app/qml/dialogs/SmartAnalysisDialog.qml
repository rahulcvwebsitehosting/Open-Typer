/*
 * SmartAnalysisDialog.qml — Smart Mistake Diagnosis (isolated from timed-para)
 * Shows *why* you mistype: adjacent keys / Shift / transposition / double-letter
 * and suggests targeted drills.  Called from ExerciseSummary or Home.qml via
 * SmartAnalyzer (C++) — no changes to ExerciseValidator path.
 */
import QtQuick 2.12
import QtQuick.Controls 2.5
import QtQuick.Controls.Material 2.5
import QtQuick.Layouts 1.12
import OpenTyper.Validator 1.0
import OpenTyper.Ui 1.0
import OpenTyper.UiComponents 1.0
import OpenTyper.Global 1.0

Dialog {
    id: root
    property string targetText: ""
    property string typedText: ""
    property real elapsedSec: 0
    property var report: null
    property bool showDrillButton: true
    signal loadDrill(string drillText)

    title: qsTr("🧠 Smart Analysis — Why You Make Mistakes")
    width: 860
    height: 640
    modal: true
    standardButtons: Dialog.Close
    Material.accent: ThemeEngine.accentColor

    SmartAnalyzer { id: analyzer }

    onTargetTextChanged: refresh()
    onTypedTextChanged: refresh()
    onOpened: refresh()

    function refresh(){
        if(targetText.length===0 || typedText.length===0){
            report = null
            return
        }
        report = analyzer.analyze(targetText, typedText)
    }

    // helper: heat color
    function heatColor(rate){
        if(rate>=0.4) return "#dc2626"
        if(rate>=0.2) return "#f87171"
        if(rate>=0.08) return "#fee2e2"
        if(rate>0) return "#fffbeb"
        return "white"
    }
    function heatTextColor(rate){
        if(rate>=0.2) return "white"
        if(rate>=0.08) return "#7f1d1d"
        if(rate>0) return "#92400e"
        return "#334155"
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // summary bar
        Rectangle {
            Layout.fillWidth: true
            height: 42
            color: "#eff6ff"
            border.color: "#bfdbfe"
            visible: report !== null
            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                Label {
                    text: report ? (report.accuracy.toFixed(1) + "%  •  " + report.errors + " errors  •  " + elapsedSec.toFixed(1) + "s") : ""
                    font.bold: true
                    color: "#0f172a"
                }
                Label {
                    text: report ? report.summary : ""
                    color: "#475569"
                    font.pointSize: 8
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                AccentButton {
                    text: qsTr("Practice Drill →")
                    visible: showDrillButton && report && report.drillText.length>0
                    onClicked: { root.loadDrill(report.drillText); root.close() }
                }
            }
        }

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            TabButton { text: qsTr("🔤 Worst Letters") }
            TabButton { text: qsTr("🔍 Why") }
            TabButton { text: qsTr("⌨ Keyboard") }
            TabButton { text: qsTr("💡 Drill") }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            // Tab 1 — worst letters
            ScrollView {
                clip: true
                ColumnLayout {
                    width: parent.width
                    spacing: 8
                    padding: 12
                    Label { text: qsTr("Letters you miss most"); font.bold:true; font.pointSize: 11 }
                    Repeater {
                        model: report ? report.worstLetters : []
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label { text: "'" + modelData.letter + "'"; font.family:"Consolas"; font.bold:true; font.pointSize:12; Layout.preferredWidth: 40 }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 18
                                color: "#f1f5f9"
                                border.color: "#e2e8f0"
                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    width: parent.width * (modelData.stats.error_rate || 0)
                                    color: modelData.stats.error_rate>=0.4 ? "#dc2626" : modelData.stats.error_rate>=0.2 ? "#f87171" : "#facc15"
                                }
                                Label {
                                    anchors.centerIn: parent
                                    text: (modelData.stats.error_rate*100).toFixed(0) + "%"
                                    color: modelData.stats.error_rate>=0.2 ? "white" : "#0f172a"
                                    font.bold:true
                                    font.pointSize: 8
                                }
                            }
                            Label { text: modelData.stats.mistakes + "/" + modelData.stats.total + "  " + modelData.stats.accuracy.toFixed(0) + "% acc"; color:"#475569"; font.pointSize:8; Layout.preferredWidth: 110 }
                        }
                    }
                    Label {
                        visible: report && report.worstBigrams.length>0
                        text: report ? ("Tricky bigrams: " + report.worstBigrams.map(function(x){ return "'" + x.bigram + "' ("+x.count+"×)" }).join(", ")) : ""
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        color: "#334155"
                        font.pointSize: 8
                    }
                    Label {
                        visible: !report || report.worstLetters.length===0
                        text: qsTr("No letter mistakes — perfect run! 🎉 Try a harder paragraph.")
                        color: "#16a34a"
                    }
                }
            }

            // Tab 2 — why
            ScrollView {
                clip:true
                ColumnLayout {
                    width: parent.width
                    padding:12
                    spacing:8
                    Label { text: qsTr("Root cause — why each mistake happened"); font.bold:true; font.pointSize:11 }
                    Repeater {
                        model: {
                            if(!report) return []
                            let cats = report.categoryCounts
                            let order = ["adjacent_key","shift_case","shift_symbol","transposition","double_letter","omission","insertion","other"]
                            let arr=[]
                            let total = 0; for(let k in cats) total+=cats[k]
                            for(let k of order){ if(cats[k]) arr.push({key:k, count:cats[k], pct: cats[k]/Math.max(1,total)*100}) }
                            return arr
                        }
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            Label {
                                text: {
                                    let m={"adjacent_key":"⌨ Adjacent / fat-finger","shift_case":"⇧ Shift / Caps","shift_symbol":"⇧ Symbol Shift","transposition":"⇄ Transposition","double_letter":"⧉ Double-letter","omission":"∅ Omission","insertion":"＋ Insertion","other":"？ Other"}
                                    return m[modelData.key] || modelData.key
                                }
                                Layout.preferredWidth: 220
                                font.pointSize: 9
                            }
                            Rectangle {
                                Layout.preferredWidth: 120
                                height: 12
                                color: "#f1f5f9"
                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    width: parent.width * modelData.pct/100
                                    color: modelData.key==="adjacent_key" ? "#0ea5e9" : modelData.key.indexOf("shift")===0 ? "#8b5cf6" : modelData.key==="transposition" ? "#f59e0b" : "#94a3b8"
                                }
                            }
                            Label { text: modelData.count + " (" + modelData.pct.toFixed(0) + "%)"; font.bold:true; font.family:"Consolas"; font.pointSize:9 }
                        }
                    }
                    Label { text: qsTr("Each mistake explained:"); font.bold:true; font.pointSize:9; topPadding:8 }
                    Repeater {
                        model: report ? report.detailed.slice(0,16) : []
                        delegate: ColumnLayout {
                            Layout.fillWidth: true
                            Label { text: "• pos " + modelData.pos + ": '" + modelData.expected + "' → '" + modelData.typed + "'  [" + modelData.category + "]"; font.family:"Consolas"; font.bold:true; font.pointSize:9; color:"#0f172a" }
                            Label { text: modelData.reason; wrapMode:Text.WordWrap; Layout.fillWidth:true; font.pointSize:8; color:"#334155" }
                            Label { text: "→ " + modelData.suggestion; wrapMode:Text.WordWrap; Layout.fillWidth:true; font.pointSize:8; color:"#0f172a"; font.italic:true; visible: modelData.suggestion && modelData.suggestion.length>0 }
                            Rectangle { Layout.fillWidth:true; height:1; color:"#f1f5f9" }
                        }
                    }
                }
            }

            // Tab 3 — keyboard heatmap
            ScrollView {
                clip:true
                ColumnLayout {
                    width: parent.width
                    padding:12
                    spacing:6
                    Label { text: qsTr("QWERTY heatmap — red = you hit this key wrong often"); font.bold:true; font.pointSize:10 }
                    Label { text: qsTr("Adjacent-key errors = wrong finger reaching neighbour key.  Shift errors = missed Shift for capitals/symbols."); wrapMode:Text.WordWrap; Layout.fillWidth:true; color:"#64748b"; font.pointSize:8 }

                    // keyboard grid
                    GridLayout {
                        columns: 13
                        rowSpacing: 6
                        columnSpacing: 6
                        // row 0
                        Repeater {
                            model: ["`","1","2","3","4","5","6","7","8","9","0","-","="]
                            delegate: Rectangle {
                                width: 44; height: 36
                                color: report ? heatColor(report.keyboardHeat[modelData] || 0) : "white"
                                border.color: "#cbd5e1"
                                Label {
                                    anchors.centerIn: parent
                                    text: modelData.toUpperCase()
                                    font.family:"Consolas"; font.bold:true; font.pointSize:9
                                    color: report ? heatTextColor(report.keyboardHeat[modelData]||0) : "#334155"
                                }
                                Label {
                                    anchors.bottom: parent.bottom
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    anchors.bottomMargin: 2
                                    visible: report && (report.keyboardHeat[modelData]||0)>0
                                    text: report ? ((report.keyboardHeat[modelData]*100).toFixed(0)+"%") : ""
                                    font.pointSize: 6
                                    color: report ? heatTextColor(report.keyboardHeat[modelData]||0) : "#334155"
                                }
                            }
                        }
                        // row 1 offset handled via empty item
                        Item { width:22; height:36; visible:false }
                        Repeater {
                            model: ["q","w","e","r","t","y","u","i","o","p","[","]","\\"]
                            delegate: Rectangle {
                                width:44; height:36
                                color: report ? heatColor(report.keyboardHeat[modelData]||0) : "white"
                                border.color: "#cbd5e1"
                                Label {
                                    anchors.centerIn: parent
                                    text: modelData.toUpperCase()
                                    font.family: "Consolas"; font.bold: true; font.pointSize: 9
                                    color: report ? heatTextColor(report.keyboardHeat[modelData]||0) : "#334155"
                                }
                                Label {
                                    anchors.bottom: parent.bottom
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    anchors.bottomMargin: 2
                                    visible: report && (report.keyboardHeat[modelData]||0)>0
                                    text: report ? ((report.keyboardHeat[modelData]*100).toFixed(0)+"%") : ""
                                    font.pointSize: 6
                                    color: report ? heatTextColor(report.keyboardHeat[modelData]||0) : "#334155"
                                }
                            }
                        }
                        // row 2
                        Item { width:22; height:36; visible:false }
                        Repeater {
                            model: ["a","s","d","f","g","h","j","k","l",";","'"]
                            delegate: Rectangle {
                                width:44; height:36
                                color: report ? heatColor(report.keyboardHeat[modelData.toLowerCase()]||report.keyboardHeat[modelData]||0) : "white"
                                border.color: "#cbd5e1"
                                Label {
                                    anchors.centerIn: parent
                                    text: modelData.toUpperCase()
                                    font.family: "Consolas"; font.bold: true; font.pointSize: 9
                                    color: report ? heatTextColor(report.keyboardHeat[modelData.toLowerCase()]||report.keyboardHeat[modelData]||0) : "#334155"
                                }
                            }
                        }
                        // row 3
                        Item { width:44; height:36; visible:false }
                        Repeater {
                            model: ["z","x","c","v","b","n","m",",",".","/"]
                            delegate: Rectangle {
                                width:44; height:36
                                color: report ? heatColor(report.keyboardHeat[modelData]||0) : "white"
                                border.color: "#cbd5e1"
                                Label {
                                    anchors.centerIn: parent
                                    text: modelData.toUpperCase()
                                    font.family: "Consolas"; font.bold: true; font.pointSize: 9
                                    color: report ? heatTextColor(report.keyboardHeat[modelData]||0) : "#334155"
                                }
                            }
                        }
                    }
                    // space
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 260; height: 32
                        color: report && (report.keyboardHeat[" "]||0)>0 ? "#fee2e2" : "white"
                        border.color: "#cbd5e1"
                        Label { anchors.centerIn: parent; text:"SPACE"; font.bold:true; color:"#334155" }
                    }
                    // legend
                    RowLayout {
                        Label { text:"0%"; color:"#475569"; font.pointSize:8 }
                        Rectangle { width:18; height:12; color:"white"; border.color:"#cbd5e1" }
                        Label { text:"1-8%"; font.pointSize:8 }
                        Rectangle { width:18; height:12; color:"#fffbeb"; border.color:"#cbd5e1" }
                        Label { text:"8-20%"; font.pointSize:8 }
                        Rectangle { width:18; height:12; color:"#fee2e2"; border.color:"#cbd5e1" }
                        Label { text:"20-40%"; font.pointSize:8 }
                        Rectangle { width:18; height:12; color:"#f87171"; border.color:"#cbd5e1" }
                        Label { text:">40%"; font.pointSize:8 }
                        Rectangle { width:18; height:12; color:"#dc2626"; border.color:"#cbd5e1" }
                    }
                }
            }

            // Tab 4 — drill
            ScrollView {
                clip:true
                ColumnLayout {
                    width: parent.width
                    padding:12
                    spacing:8
                    Label { text: qsTr("Personalized suggestions"); font.bold:true; font.pointSize:11 }
                    Repeater {
                        model: report ? report.suggestions : []
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing:8
                            Rectangle { width:6; height:6; radius:3; color:"#0ea5e9"; Layout.alignment: Qt.AlignTop; Layout.topMargin:6 }
                            Label { text: modelData; wrapMode:Text.WordWrap; Layout.fillWidth:true; font.pointSize:9; color:"#0f172a" }
                        }
                    }
                    Rectangle { Layout.fillWidth:true; height:1; color:"#e2e8f0" }
                    Label { text: qsTr("Your custom drill (focuses on weakest letters):"); font.bold:true; font.pointSize:10 }
                    Label { text: qsTr("Click 'Practice Drill →' to load as custom exercise, or copy below."); color:"#64748b"; font.pointSize:8; wrapMode:Text.WordWrap; Layout.fillWidth:true }
                    TextArea {
                        Layout.fillWidth: true
                        readOnly: true
                        wrapMode: TextArea.Wrap
                        text: report ? report.drillText : ""
                        font.family: "Consolas"
                        font.pointSize: 9
                        background: Rectangle { color:"#fffbeb"; border.color:"#fde68a" }
                    }
                }
            }
        }
    }
}
