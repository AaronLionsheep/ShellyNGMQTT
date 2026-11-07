let BTHOME_SVC_ID = "fcd2";

function BLEScanCallback(event, result) {
  if (event !== BLE.Scanner.SCAN_RESULT) return;
  if (typeof result !== "object") return;
  if (!result.service_data || !result.service_data[BTHOME_SVC_ID]) return;
  let data = { version: 1, address: result.addr, rssi: result.rssi, service_data: {} };
  data.service_data[BTHOME_SVC_ID] = btoh(result.service_data[BTHOME_SVC_ID]);
  Shelly.emitEvent("shelly-blu", data);
}

function init() {
  if (Shelly.getComponentConfig("ble").enable === false) {
    console.log("Error: Bluetooth must be enabled!");
    return;
  }

  // Always request a scan: the 1.5+ scan manager requires it. Before 1.5,
  // Start fails if another client owns the scan, but Subscribe still gets its results.
  BLE.Scanner.Start({ duration_ms: BLE.Scanner.INFINITE_SCAN, active: false });
  BLE.Scanner.Subscribe(BLEScanCallback);
}

init();