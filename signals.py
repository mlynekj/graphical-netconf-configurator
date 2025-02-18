from PySide6.QtCore import QObject, Signal

class SignalManager(QObject):
    # Emited when a pending change is added to the device:
    #   (helper.py - "helper.addPendingChange").
    # Connects to function that adds the change to the pending changes table:
    #   (main.py - pendingChangesDockWidget.addPendingChangeToTable).
    pendingChangeAdded = Signal(object, str, str, str) # (device_id, pending_change_name, rpc_reply, filter)

    # Emited when the device no longer has any pending changes - either by discarding or by commiting them:
    #   (devices.py - "device.discardChanges", "device.commitChanges").
    # Connects to function that clears the pending changes for the device from the pending changes table:
    #   (main.py - pendingChangesDockWidget.clearPendingChangesFromTable).
    deviceNoLongerHasPendingChanges = Signal(object)

signal_manager = SignalManager()