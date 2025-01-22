from PySide6.QtCore import QObject, Signal

class SignalManager(QObject):
    pendingChangeAdded = Signal(object, str)
    pendingChangeRemoved = Signal(object, str)

signal_manager = SignalManager()