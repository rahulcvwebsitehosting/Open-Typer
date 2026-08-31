TEMPLATE = lib
QT += core qml
CONFIG += staticlib

SOURCES += \
    ValidatorModule.cpp \
    SmartAnalyzer.cpp \
    internal/ExerciseValidator.cpp

HEADERS += \
    CharacterRecord.h \
    IExerciseValidator.h \
    MistakeRecord.h \
    SmartAnalyzer.h \
    ValidatorModule.h \
    internal/ExerciseValidator.h
