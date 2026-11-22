let S = BLE.Scanner;

// 1.5+ needs a scan request. Before 1.5, Start returns null if another
// client owns the scan, but Subscribe still gets results.
function scan() {
  if (S.Start({ duration_ms: S.INFINITE_SCAN, active: false }) !== null) return;
  console.log(S.isRunning() ? "BLE scan owned by other client" : "Error: BLE scan failed!");
}

function onScan(event, res) {
  // Before 1.5, another client's scan can stop: rescan
  if (event === S.SCAN_STOP) return scan();
  if (event !== S.SCAN_RESULT || typeof res !== "object") return;
  // fcd2 is the BTHome service UUID
  let sd = res.service_data;
  if (!sd || !sd.fcd2) return;
  Shelly.emitEvent("indigo-blu-relay", { version: 1, address: res.addr, rssi: res.rssi, service_data: { fcd2: btoh(sd.fcd2) } });
}

if (Shelly.getComponentConfig("ble").enable === false) {
  console.log("Error: Bluetooth must be enabled!");
} else {
  scan();
  S.Subscribe(onScan);
}
