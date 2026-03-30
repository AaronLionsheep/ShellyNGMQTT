let BTHOME_SVC_ID = "fcd2";

function BLEScanCallback(event, result) {
  if (event !== BLE.Scanner.SCAN_RESULT) return;
  if (typeof result !== "object") return;
  if (!result.service_data || !result.service_data[BTHOME_SVC_ID]) return;
  let data = { address: result.addr, rssi: result.rssi, service_data: {}, keys: Object.keys(result) };
  data.service_data[BTHOME_SVC_ID] = btoh(result.service_data[BTHOME_SVC_ID]);
  Shelly.emitEvent("shelly-blu", data);
}

function init() {
  if (!Shelly.getComponentConfig("ble").enable) {
    console.log("Error: Bluetooth must be enabled!");
    return;
  }

  if (BLE.Scanner.isRunning()) {
    console.log("Info: The BLE gateway is running.");
  } else {
    let bleScanner = BLE.Scanner.Start({ duration_ms: BLE.Scanner.INFINITE_SCAN, active: false });
    if(!bleScanner) console.log("Error: Can not start new scanner!");
  }

  BLE.Scanner.Subscribe(BLEScanCallback);
}

init();