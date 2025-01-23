from PySide6.QtCore import QObject, Signal

class SignalManager(QObject):
    pendingChangeAdded = Signal(object, str)
    allPendingChangesDiscarded = Signal(object)

signal_manager = SignalManager()