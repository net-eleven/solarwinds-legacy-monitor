import time
from datetime import datetime, timedelta
import winsound
from winotify import Notification, audio
from login import OrionClient
from fetch import Fetch
import parse

# Configuration
POLL_INTERVAL_SECONDS = 120    # Poll SolarWinds every 2 minutes
FLAP_HOLD_MINUTES = 10         # Hold time before initial alert
REMINDER_INTERVAL_MINUTES = 30 # Re-alert interval for ongoing down links
SHIFT_START_TIME = "11:30 AM"  # Shift start cutoff time

def format_duration(total_minutes):
    """Converts total minutes into human-readable duration string."""
    mins = int(total_minutes)
    if mins < 60:
        return f"{mins}m"
    
    hours = mins // 60
    rem_mins = mins % 60
    h_label = "hour" if hours == 1 else "hours"
    
    if rem_mins == 0:
        return f"{hours} {h_label}"
    return f"{hours} {h_label} {rem_mins}m"

def parse_timestamp(d_str):
    """Parses SolarWinds downtime string into a datetime object."""
    try:
        return datetime.strptime(d_str, "%d-%b-%y %I:%M %p")
    except Exception:
        return None

def get_shift_start_datetime(time_str):
    """Converts '04:00 PM' or '11-Aug-26 04:00 PM' into a full datetime object."""
    now = datetime.now()
    time_str = time_str.strip()

    # Try parsing full date + time
    for fmt in ("%d-%b-%y %I:%M %p", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            pass

    # Fallback to time-only string
    try:
        parsed_time = datetime.strptime(time_str, "%I:%M %p").time()
    except ValueError:
        parsed_time = datetime.strptime(time_str, "%H:%M").time()

    shift_dt = datetime.combine(now.date(), parsed_time)
    
    # Midnight crossover check
    if shift_dt > now:
        shift_dt -= timedelta(days=1)
        
    return shift_dt

def send_windows_toast(title, msg, icon_style="Critical"):
    """Fires a native Windows 10/11 Action Center notification."""
    try:
        toast = Notification(
            app_id="NOC Shift Monitor",
            title=title,
            msg=msg,
            duration="long"
        )
        if icon_style == "Critical":
            toast.set_audio(audio.LoopingAlarm, loop=False)
        else:
            toast.set_audio(audio.Default, loop=False)
        toast.show()
    except Exception as e:
        print(f"[!] Windows Toast Error: {e}")

def sound_alarm():
    """Plays an alert chime on Windows."""
    try:
        winsound.Beep(1000, 400)
        winsound.Beep(1000, 400)
    except Exception:
        print("\a")  # Fallback terminal bell

def main():
    shift_start_dt = get_shift_start_datetime(SHIFT_START_TIME)

    print("==================================================")
    print("   NOC SHIFT LIVE MONITOR (WINDOWS TERMINAL)     ")
    print("==================================================")
    print(f"[*] Polling Interval : Every {POLL_INTERVAL_SECONDS // 60} minutes")
    print(f"[*] Flap Hold Timer  : {FLAP_HOLD_MINUTES} minutes before alerting")
    print(f"[*] Reminder Timer   : Every {REMINDER_INTERVAL_MINUTES} minutes")
    print(f"[*] Shift Start Cutoff: {shift_start_dt.strftime('%d-%b-%Y %I:%M %p')}")
    print("==================================================\n")

    client = OrionClient()
    if not client.authenticate():
        print("[-] Exiting due to authentication failure.")
        return

    fetcher = Fetch()
    tracked_state = {}
    is_first_run = True

    try:
        while True:
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now_str}] Polling SolarWinds...")

            # 1. Fetch current down items
            node_html = fetcher.fetch_nodes(client)
            raw_nodes = parse.parse_report_html(node_html, "Node") if node_html else []
            
            interface_html = fetcher.fetch_interfaces(client)
            raw_interfaces = parse.parse_report_html(interface_html, "Interface") if interface_html else []

            raw_all = raw_nodes + raw_interfaces
            current_active_keys = set()

            # Batch lists for grouping output
            new_outages = []
            initial_alerts = []
            periodic_reminders = []
            recovered_items = []
            flap_items = []

            # 2. Process fetched items
            for item in raw_all:
                downtime_str = fetcher.fetch_downtime(client, item)
                item_dt = parse_timestamp(downtime_str)

                # Skip outages that occurred BEFORE shift start time
                if item_dt and item_dt < shift_start_dt:
                    continue

                # Build unique key and label
                if item['type'] == 'Interface':
                    label = f"{item['parent']} -> {item['name']}"
                    key = f"INT:{label}"
                else:
                    label = item['name']
                    key = f"NODE:{label}"

                current_active_keys.add(key)

                # Add new item to tracked state
                if key not in tracked_state:
                    tracked_state[key] = {
                        "first_seen": item_dt if item_dt else now,
                        "initial_alerted": False,
                        "last_alerted": None,
                        "display_name": label,
                        "solarwinds_time": downtime_str
                    }
                    if not is_first_run:
                        new_outages.append(label)

            # 3. Process hold timers & reminders
            for key, data in list(tracked_state.items()):
                if key in current_active_keys:
                    total_minutes_down = (now - data["first_seen"]).total_seconds() / 60.0
                    dur_str = format_duration(total_minutes_down)

                    # CASE A: Initial Alert
                    if total_minutes_down >= FLAP_HOLD_MINUTES and not data["initial_alerted"]:
                        data["initial_alerted"] = True
                        data["last_alerted"] = now
                        initial_alerts.append((dur_str, data["display_name"]))

                    # CASE B: Periodic Reminder
                    elif data["initial_alerted"] and data["last_alerted"]:
                        mins_since_last_alert = (now - data["last_alerted"]).total_seconds() / 60.0
                        if mins_since_last_alert >= REMINDER_INTERVAL_MINUTES:
                            data["last_alerted"] = now
                            periodic_reminders.append((dur_str, data["display_name"]))

            # 4. Process recovered items and flaps
            tracked_keys = list(tracked_state.keys())
            for key in tracked_keys:
                if key not in current_active_keys:
                    item = tracked_state.pop(key)
                    if item.get("initial_alerted", False):
                        recovered_items.append(item["display_name"])
                    else:
                        total_down = (now - item["first_seen"]).total_seconds() / 60.0
                        dur_str = format_duration(total_down)
                        flap_items.append((dur_str, item["display_name"]))

            # ---------------- DISPLAY BATCHED OUTPUTS ----------------

            # 1. NEW SHIFT OUTAGES (Detected, currently holding for 10m)
            if new_outages:
                print(f"\n🔍 NEW SHIFT OUTAGES ({len(new_outages)} Detected - Holding {FLAP_HOLD_MINUTES}m):")
                for name in new_outages:
                    print(f"  • {name}")

            # 2. INITIAL ALERTS (Down >= 10m)
            if initial_alerts:
                print(f"\n🚨 INITIAL ALERTS ({len(initial_alerts)} Outages >= {FLAP_HOLD_MINUTES}m):")
                for dur, name in initial_alerts:
                    time_col = f"[{dur}]".ljust(18)
                    print(f"  • {time_col} │ {name}")
                sound_alarm()
                
                toast_body = f"[{initial_alerts[0][0]}] {initial_alerts[0][1]}" if len(initial_alerts) == 1 else f"{len(initial_alerts)} new links down > {FLAP_HOLD_MINUTES}m"
                send_windows_toast("🚨 NOC Outage Alert", toast_body, icon_style="Critical")

            # 3. PERIODIC REMINDERS (Still down after 30m)
            if periodic_reminders:
                print(f"\n⏰ PERIODIC REMINDERS ({len(periodic_reminders)} Still Active):")
                for dur, name in periodic_reminders:
                    time_col = f"[{dur}]".ljust(18)
                    print(f"  • {time_col} │ {name}")
                sound_alarm()
                
                toast_body = f"[{periodic_reminders[0][0]} total] {periodic_reminders[0][1]}" if len(periodic_reminders) == 1 else f"{len(periodic_reminders)} outages still active"
                send_windows_toast("⏰ Outage Still Active", toast_body, icon_style="Normal")

            # 4. RESOLVED OUTAGES (Recovered after initial alert fired)
            if recovered_items:
                print(f"\n✅ RESOLVED OUTAGES ({len(recovered_items)} Restored):")
                for name in recovered_items:
                    print(f"  • {name}")
                
                toast_body = recovered_items[0] if len(recovered_items) == 1 else f"{len(recovered_items)} links recovered"
                send_windows_toast("✅ Link Recovered", toast_body, icon_style="Normal")

            # 5. FLAPS RESOLVED (Recovered under 10m before alert fired)
            if flap_items:
                print(f"\n⚡ FLAPS RESOLVED ({len(flap_items)} Recovered < {FLAP_HOLD_MINUTES}m):")
                for dur, name in flap_items:
                    time_col = f"[{dur}]".ljust(18)
                    print(f"  • {time_col} │ {name}")

            if is_first_run:
                is_first_run = False
                print(f"[*] Initial baseline set. Monitoring {len(tracked_state)} outages from current shift...")

            print(f"[*] Cycle complete. Next check in {POLL_INTERVAL_SECONDS} seconds...\n")
            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[!] Monitor stopped by user.")

if __name__ == "__main__":
    main()