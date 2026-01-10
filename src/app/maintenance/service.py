from pathlib import Path

from app.core.utils import run_command

from .schemas import RebootFrequency, RebootScheduleRequest, RebootScheduleResponse

CRON_FILE = Path("/etc/cron.d/streamcloak-reboot")
REBOOT_CMD = "root /sbin/shutdown -r now"


class MaintenanceService:
    @staticmethod
    def get_reboot_schedule() -> RebootScheduleResponse:
        """
        Reads the cron file and parses valid cron expressions back into the Schema.
        """
        if not CRON_FILE.exists():
            # Default return if no file exists
            return RebootScheduleResponse(
                frequency=RebootFrequency.DISABLED,
                time="03:00",  # Default fallback
                day_of_week=0,
                day_of_month=1,
            )

        try:
            # Read file content
            content = CRON_FILE.read_text().strip()

            # Expected format: "MM HH DOM MON DOW root /sbin/shutdown -r now"
            # Example: "0 3 * * 3 root /sbin/shutdown -r now"

            parts = content.split()
            if len(parts) < 6:
                raise ValueError("Invalid cron format")

            minute = parts[0]
            hour = parts[1]
            dom = parts[2]  # Day of Month
            # month = parts[3] (Always * for us)
            dow = parts[4]  # Day of Week

            time_str = f"{int(hour):02d}:{int(minute):02d}"

            # Determine Logic
            if dom == "*" and dow == "*":
                frequency = RebootFrequency.DAILY
                day_of_week = 0
                day_of_month = 1
            elif dom == "*" and dow != "*":
                frequency = RebootFrequency.WEEKLY
                day_of_week = int(dow)
                day_of_month = 1
            elif dom != "*" and dow == "*":
                frequency = RebootFrequency.MONTHLY
                day_of_week = 0
                day_of_month = int(dom)
            else:
                # Fallback / Unknown / Custom
                frequency = RebootFrequency.DISABLED
                day_of_week = 0
                day_of_month = 1

            return RebootScheduleResponse(
                frequency=frequency, time=time_str, day_of_week=day_of_week, day_of_month=day_of_month
            )

        except Exception as e:
            print(f"Error parsing reboot schedule: {e}")
            # Return disabled on error to be safe
            return RebootScheduleResponse(frequency=RebootFrequency.DISABLED, time="00:00")

    @staticmethod
    def set_reboot_schedule(data: RebootScheduleRequest):
        """
        Generates the cron content and writes it to /etc/cron.d/
        """

        # If DISABLED, remove the main file and return
        if data.frequency == RebootFrequency.DISABLED:
            if CRON_FILE.exists():
                run_command(["sudo", "rm", str(CRON_FILE)])
            return {"status": "disabled"}

        # 3. Parse time
        hour, minute = data.time.split(":")

        # 4. Construct Cron parts
        # Format: m h dom mon dow
        cron_m = str(int(minute))
        cron_h = str(int(hour))
        cron_dom = "*"
        cron_mon = "*"
        cron_dow = "*"

        if data.frequency == RebootFrequency.DAILY:
            # * * * (Every day)
            pass
        elif data.frequency == RebootFrequency.WEEKLY:
            # * * D (Specific day of week)
            cron_dow = str(data.day_of_week)
        elif data.frequency == RebootFrequency.MONTHLY:
            # D * * (Specific day of month)
            cron_dom = str(data.day_of_month)

        # 5. Build the full string
        # e.g.: "0 3 * * 3 root /sbin/shutdown -r now"
        cron_job = f"{cron_m} {cron_h} {cron_dom} {cron_mon} {cron_dow} {REBOOT_CMD}"

        # 6. Write to file using sudo tee
        # We write to a temporary string then pipe to tee
        cmd = f"echo '{cron_job}' | sudo tee {str(CRON_FILE)} > /dev/null"

        # Since run_command expects a list for subprocess usually, but piping is shell feature.
        # We need to run this as shell=True or wrap in sh -c
        run_command(["sudo", "sh", "-c", cmd])

        # 7. Set permissions
        run_command(["sudo", "chmod", "644", str(CRON_FILE)])

        return {"status": "updated", "cron_entry": cron_job}
